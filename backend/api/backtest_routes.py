"""
Backtest API Routes

FastAPI routes for handling backtest report uploads, comparisons, and deviation analysis.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel
import logging
from typing import Dict, List, Optional
import os
import tempfile
import sqlite3
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Initialize backtest service
backtest_service = None
try:
    from database.connection import get_database_manager
    from services.backtest_service import BacktestService
    db_manager = get_database_manager()
    backtest_service = BacktestService(db_manager)
    logger.info("BacktestService initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize BacktestService: {e}")
    backtest_service = None

def get_db_connection():
    """Get database connection"""
    if "DATABASE_PATH" in os.environ:
        db_path = os.getenv("DATABASE_PATH")
    else:
        # Get absolute path to database file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(current_dir)
        db_path = os.path.join(backend_dir, "data", "mt5_dashboard.db")
    return sqlite3.connect(db_path)

def parse_backtest_html_simple(html_content: str) -> Optional[Dict]:
    """Simple backtest HTML parser for MT5 Strategy Tester reports"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all table cells with <b> tags (bold values)
        bold_cells = soup.find_all('b')
        
        metrics = {}
        
        # Look for specific patterns in the HTML structure
        for i, cell in enumerate(bold_cells):
            cell_text = cell.get_text().strip()
            
            # Find the previous cell to get the label
            parent_td = cell.find_parent('td')
            if parent_td:
                parent_tr = parent_td.find_parent('tr')
                if parent_tr:
                    all_tds = parent_tr.find_all('td')
                    
                    # Look for labels in the same row
                    for td in all_tds:
                        label_text = td.get_text().strip().lower()
                        
                        # Profit Factor
                        if 'profit factor' in label_text and cell_text.replace('.', '').isdigit():
                            try:
                                metrics['profit_factor'] = float(cell_text)
                            except ValueError:
                                pass
                        
                        # Expected Payoff
                        elif 'expected payoff' in label_text:
                            try:
                                # Handle negative values
                                value = cell_text.replace('-', '').replace('+', '')
                                if value.replace('.', '').isdigit():
                                    metrics['expected_payoff'] = float(cell_text)
                            except ValueError:
                                pass
                        
                        # Drawdown (look for percentage in parentheses)
                        elif 'drawdown' in label_text and 'maximal' in label_text:
                            # Look for pattern like "318.96 (5.81%)"
                            drawdown_match = re.search(r'\(([\d\.]+)%\)', cell_text)
                            if drawdown_match:
                                try:
                                    metrics['drawdown'] = float(drawdown_match.group(1))
                                except ValueError:
                                    pass
                        
                        # Total Deals (trade count)
                        elif 'total deals' in label_text and cell_text.isdigit():
                            try:
                                metrics['trade_count'] = int(cell_text)
                            except ValueError:
                                pass
                        
                        # Win Rate (from Profit Trades)
                        elif 'profit trades' in label_text and '(' in cell_text:
                            # Look for pattern like "670 (77.19%)"
                            win_rate_match = re.search(r'\(([\d\.]+)%\)', cell_text)
                            if win_rate_match:
                                try:
                                    metrics['win_rate'] = float(win_rate_match.group(1))
                                except ValueError:
                                    pass
        
        # Debug output
        print(f"🔍 Parsed metrics: {metrics}")
        
        # Return metrics if we found at least 3 key metrics
        if len(metrics) >= 3:
            return metrics
        else:
            # Fallback: try regex patterns on the full text
            text_content = soup.get_text()
            
            fallback_patterns = {
                'profit_factor': r'Profit\s+Factor:\s*([\d\.]+)',
                'expected_payoff': r'Expected\s+Payoff:\s*([\d\.\-]+)',
                'drawdown': r'Drawdown.*?\(([\d\.]+)%\)',
                'win_rate': r'Profit\s+Trades.*?\(([\d\.]+)%\)',
                'trade_count': r'Total\s+Deals:\s*(\d+)'
            }
            
            for metric_name, pattern in fallback_patterns.items():
                match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        value = float(match.group(1))
                        metrics[metric_name] = value
                    except (ValueError, IndexError):
                        continue
            
            print(f"🔍 Fallback parsed metrics: {metrics}")
            return metrics if len(metrics) >= 3 else None
        
    except Exception as e:
        logger.error(f"Error parsing backtest HTML: {e}")
        return None

# Pydantic models
class LiveMetrics(BaseModel):
    profit_factor: float = 0.0
    expected_payoff: float = 0.0
    drawdown: float = 0.0
    total_profit: float = 0.0
    trade_count: int = 0
    z_score: float = 0.0

class CompareRequest(BaseModel):
    ea_id: int
    live_metrics: LiveMetrics

@router.get("/benchmarks")
async def get_backtest_benchmarks():
    """Get all backtest benchmarks"""
    try:
        logger.info("📊 GET /api/backtest/benchmarks called")
        
        if backtest_service:
            logger.info("✅ BacktestService is available, using it")
            # Use BacktestService to get benchmarks
            try:
                from models.performance import BacktestBenchmark
                
                with backtest_service.db.get_session() as session:
                    benchmarks_query = session.query(BacktestBenchmark).order_by(BacktestBenchmark.upload_date.desc()).all()
                    logger.info(f"🔍 Found {len(benchmarks_query)} benchmarks in database via SQLAlchemy")
                    
                    benchmarks = []
                    for benchmark in benchmarks_query:
                        benchmarks.append({
                            'ea_id': benchmark.ea_id,
                            'profit_factor': benchmark.profit_factor,
                            'expected_payoff': benchmark.expected_payoff,
                            'drawdown': benchmark.drawdown,
                            'win_rate': benchmark.win_rate,
                            'trade_count': benchmark.trade_count,
                            'upload_date': benchmark.upload_date.isoformat() if benchmark.upload_date else None
                        })
                    
                    # Get summary from service
                    summary = backtest_service.get_benchmark_summary()
                    
                    logger.info(f"📊 Returning {len(benchmarks)} benchmarks using BacktestService")
                    
                    return {
                        'success': True,
                        'benchmarks': benchmarks,
                        'summary': summary,
                        'source': 'backtest_service',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except Exception as service_error:
                logger.error(f"❌ BacktestService failed: {service_error}")
                logger.warning("🔄 Falling back to direct database access")
        else:
            logger.warning("⚠️ BacktestService not available, using direct database access")
        
        # Fallback to direct database access
        logger.info("🔍 Using direct database connection")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if table exists first
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='backtest_benchmarks'
        """)
        
        if not cursor.fetchone():
            logger.warning("❌ backtest_benchmarks table does not exist")
            conn.close()
            return {
                'success': True,
                'benchmarks': [],
                'summary': {
                    'total_benchmarks': 0,
                    'avg_profit_factor': 0,
                    'avg_drawdown': 0
                },
                'source': 'database_fallback',
                'message': 'Table does not exist'
            }
        
        # Get all benchmarks
        cursor.execute("""
            SELECT ea_id, profit_factor, expected_payoff, drawdown, 
                   win_rate, trade_count, upload_date
            FROM backtest_benchmarks 
            ORDER BY upload_date DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        logger.info(f"🔍 Found {len(rows)} benchmarks in database via direct SQL")
        
        # Convert to list of dictionaries
        benchmarks = []
        for row in rows:
            benchmarks.append({
                'ea_id': row[0],
                'profit_factor': row[1],
                'expected_payoff': row[2],
                'drawdown': row[3],
                'win_rate': row[4],
                'trade_count': row[5],
                'upload_date': row[6]
            })
        
        # Calculate summary
        if benchmarks:
            avg_profit_factor = sum(b['profit_factor'] for b in benchmarks) / len(benchmarks)
            avg_drawdown = sum(b['drawdown'] for b in benchmarks) / len(benchmarks)
        else:
            avg_profit_factor = 0
            avg_drawdown = 0
        
        logger.info(f"📊 Returning {len(benchmarks)} benchmarks from direct database")
        
        response_data = {
            'success': True,
            'benchmarks': benchmarks,
            'summary': {
                'total_benchmarks': len(benchmarks),
                'avg_profit_factor': round(avg_profit_factor, 2),
                'avg_drawdown': round(avg_drawdown, 2)
            },
            'source': 'database_fallback',
            'timestamp': datetime.now().isoformat()
        }
        
        # Add cache-busting headers
        from fastapi import Response
        response = Response(
            content=json.dumps(response_data),
            media_type="application/json",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting backtest benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deviations")
async def get_deviation_reports():
    """Get deviation reports for all EAs with backtest benchmarks"""
    try:
        if backtest_service:
            try:
                # Get real deviation reports
                deviation_reports = backtest_service.get_all_deviations()
                return {
                    'success': True,
                    'deviations': [report.to_dict() for report in deviation_reports],
                    'count': len(deviation_reports),
                    'source': 'backtest_service'
                }
            except Exception as e:
                logger.error(f"Failed to get real deviations: {e}")
                return {
                    'success': False,
                    'deviations': [],
                    'count': 0,
                    'error': str(e),
                    'source': 'backtest_service_failed'
                }
        
    except Exception as e:
        logger.error(f"Error getting deviation reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_backtest_report(
    ea_id: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload backtest HTML report for an EA"""
    print(f"🔄 Backtest upload for EA {ea_id}")
    
    try:
        # Validate file type
        if not file.filename.endswith(('.html', '.htm')):
            raise HTTPException(
                status_code=400, 
                detail="File must be an HTML backtest report"
            )
        
        # Read file content with proper encoding handling
        content = await file.read()
        
        # Try different encodings
        html_content = None
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                html_content = content.decode(encoding)
                print(f"✅ Successfully decoded with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        # Fallback to utf-8 with error handling
        if html_content is None:
            html_content = content.decode('utf-8', errors='ignore')
            print("✅ Decoded with utf-8 and error handling")
        
        print(f"📖 File read: {len(html_content)} characters")
        
        # Parse the HTML report
        metrics = parse_backtest_html_simple(html_content)
        if not metrics:
            raise HTTPException(
                status_code=400,
                detail="Failed to parse backtest report. Please ensure it's a valid MT5 backtest HTML file."
            )
        
        print(f"✅ Parsed metrics: {metrics}")
        
        # Store in database using BacktestService
        try:
            if backtest_service:
                # Use BacktestService to store the benchmark
                from services.backtest_parser import BacktestMetrics
                
                backtest_metrics = BacktestMetrics(
                    profit_factor=metrics.get('profit_factor', 0.0),
                    expected_payoff=metrics.get('expected_payoff', 0.0),
                    drawdown=metrics.get('drawdown', 0.0),
                    win_rate=metrics.get('win_rate', 0.0),
                    trade_count=int(metrics.get('trade_count', 0))
                )
                
                success = backtest_service._store_backtest_benchmark(ea_id, backtest_metrics)
                if not success:
                    raise HTTPException(status_code=500, detail="Failed to store benchmark using BacktestService")
                
                print(f"✅ Stored benchmark for EA {ea_id} using BacktestService")
            else:
                # Fallback to direct database access
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Create table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS backtest_benchmarks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ea_id INTEGER NOT NULL,
                        profit_factor REAL NOT NULL,
                        expected_payoff REAL NOT NULL,
                        drawdown REAL NOT NULL,
                        win_rate REAL NOT NULL,
                        trade_count INTEGER NOT NULL,
                        upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(ea_id)
                    )
                """)
                
                # Insert or replace benchmark
                cursor.execute("""
                    INSERT OR REPLACE INTO backtest_benchmarks 
                    (ea_id, profit_factor, expected_payoff, drawdown, win_rate, trade_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ea_id,
                    metrics.get('profit_factor', 0.0),
                    metrics.get('expected_payoff', 0.0),
                    metrics.get('drawdown', 0.0),
                    metrics.get('win_rate', 0.0),
                    int(metrics.get('trade_count', 0))
                ))
                
                conn.commit()
                conn.close()
                print(f"✅ Stored benchmark for EA {ea_id} using direct database")
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        return {
            "success": True,
            "message": f"Backtest report uploaded successfully for EA {ea_id}",
            "ea_id": ea_id,
            "metrics": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/compare/{ea_id}")
async def compare_ea_performance(ea_id: int):
    """Compare live EA performance with backtest benchmark"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get backtest benchmark
        cursor.execute("""
            SELECT profit_factor, expected_payoff, drawdown, win_rate, trade_count
            FROM backtest_benchmarks 
            WHERE ea_id = ?
        """, (ea_id,))
        
        benchmark_row = cursor.fetchone()
        if not benchmark_row:
            conn.close()
            raise HTTPException(
                status_code=404, 
                detail=f"No backtest benchmark found for EA {ea_id}"
            )
        
        # Mock live performance for demo (would get from performance_history table)
        live_pf = benchmark_row[0] * 0.85  # 15% worse
        live_ep = benchmark_row[1] * 0.90  # 10% worse
        live_dd = benchmark_row[2] * 1.20  # 20% higher drawdown
        
        conn.close()
        
        # Calculate deviations
        pf_deviation = ((live_pf - benchmark_row[0]) / benchmark_row[0] * 100) if benchmark_row[0] != 0 else 0
        ep_deviation = ((live_ep - benchmark_row[1]) / benchmark_row[1] * 100) if benchmark_row[1] != 0 else 0
        dd_deviation = ((live_dd - benchmark_row[2]) / benchmark_row[2] * 100) if benchmark_row[2] != 0 else 0
        
        # Determine status
        overall_status = "good"
        if abs(pf_deviation) > 20 or abs(ep_deviation) > 25 or dd_deviation > 50:
            overall_status = "critical"
        elif abs(pf_deviation) > 10 or abs(ep_deviation) > 15 or dd_deviation > 25:
            overall_status = "warning"
        
        return {
            "success": True,
            "ea_id": ea_id,
            "comparison": {
                "overall_status": overall_status,
                "profit_factor_deviation": round(pf_deviation, 2),
                "expected_payoff_deviation": round(ep_deviation, 2),
                "drawdown_deviation": round(dd_deviation, 2)
            },
            "backtest_benchmark": {
                "profit_factor": benchmark_row[0],
                "expected_payoff": benchmark_row[1],
                "drawdown": benchmark_row[2],
                "win_rate": benchmark_row[3],
                "trade_count": benchmark_row[4]
            },
            "live_performance": {
                "profit_factor": live_pf,
                "expected_payoff": live_ep,
                "drawdown": live_dd
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/benchmark/{ea_id}")
async def get_ea_benchmark(ea_id: int):
    """Get backtest benchmark for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT profit_factor, expected_payoff, drawdown, win_rate, 
                   trade_count, upload_date
            FROM backtest_benchmarks 
            WHERE ea_id = ?
            ORDER BY upload_date DESC 
            LIMIT 1
        """, (ea_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No backtest benchmark found for EA {ea_id}"
            )
        
        return {
            'success': True,
            'ea_id': ea_id,
            'benchmark': {
                'profit_factor': row[0],
                'expected_payoff': row[1],
                'drawdown': row[2],
                'win_rate': row[3],
                'trade_count': row[4],
                'upload_date': row[5]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Benchmark retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark: {str(e)}")


@router.delete("/benchmark/{ea_id}")
async def delete_ea_benchmark(ea_id: int):
    """Delete backtest benchmark for specific EA"""
    try:
        if not backtest_service:
            raise HTTPException(
                status_code=503,
                detail="Backtest service not available"
            )
        
        success = backtest_service.delete_backtest_benchmark(ea_id)
        if success:
            return {
                'success': True,
                'message': f'Backtest benchmark deleted for EA {ea_id}'
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No benchmark found for EA {ea_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting benchmark for EA {ea_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flagged-eas")
async def get_flagged_eas():
    """Get list of EAs flagged for demotion due to poor performance"""
    try:
        if backtest_service:
            try:
                flagged_eas = backtest_service.get_eas_flagged_for_demotion()
                return {
                    'success': True,
                    'flagged_eas': flagged_eas,
                    'count': len(flagged_eas),
                    'source': 'backtest_service'
                }
            except Exception as e:
                logger.error(f"Failed to get flagged EAs: {e}")
                return {
                    'success': False,
                    'flagged_eas': [],
                    'count': 0,
                    'error': str(e),
                    'source': 'backtest_service_failed'
                }
        
    except Exception as e:
        logger.error(f"Error getting flagged EAs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for backtest service"""
    try:
        if backtest_service:
            summary = backtest_service.get_benchmark_summary()
            return {
                'status': 'healthy',
                'service': 'backtest_service',
                'benchmarks_count': summary.get('total_benchmarks', 0),
                'database_connected': True
            }
        else:
            return {
                'status': 'degraded',
                'service': 'backtest_service',
                'benchmarks_count': 0,
                'database_connected': False,
                'message': 'BacktestService not initialized - check database connection'
            }
        
    except Exception as e:
        logger.error(f"Backtest service health check failed: {e}")
        return {
            'status': 'unhealthy',
            'service': 'backtest_service',
            'error': str(e)
        }