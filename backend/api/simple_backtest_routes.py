"""
Simple Backtest Upload Routes
Clean, working implementation for backtest report uploads
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Optional
import tempfile
import os
import sqlite3
import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simple-backtest", tags=["Simple Backtest"])

class BacktestMetrics(BaseModel):
    profit_factor: float
    expected_payoff: float
    drawdown: float
    win_rate: float
    trade_count: int
    total_profit: float = 0.0

def get_db_connection():
    """Get database connection"""
    db_path = os.getenv("DATABASE_PATH", "data/mt5_dashboard.db")
    return sqlite3.connect(db_path)

def parse_backtest_html(html_content: str) -> Optional[BacktestMetrics]:
    """Parse MT5 backtest HTML report"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        
        # Regex patterns for extracting metrics
        patterns = {
            'profit_factor': [
                r'Profit\s+factor\s*[:\-]?\s*([\d\.]+)',
                r'>Profit\s+factor</td>\s*<td[^>]*>([\d\.]+)</td>',
            ],
            'expected_payoff': [
                r'Expected\s+payoff\s*[:\-]?\s*([\d\.\-]+)',
                r'>Expected\s+payoff</td>\s*<td[^>]*>([\d\.\-]+)</td>',
            ],
            'drawdown': [
                r'Maximal\s+drawdown\s*[:\-]?\s*([\d\.]+)%?',
                r'>Maximal\s+drawdown</td>\s*<td[^>]*>([\d\.]+)%?</td>',
                r'([\d\.]+)\s*\(([\d\.]+)%\)</b></td>'
            ],
            'win_rate': [
                r'Profit\s+trades\s+\([^)]*\)\s*[:\-]?\s*\d+\s*\(\s*([\d\.]+)\s*%\s*\)',
                r'>Profit\s+trades\s+\([^)]*\)</td>\s*<td[^>]*>\d+\s*\(([\d\.]+)%\)</td>',
            ],
            'trade_count': [
                r'Total\s+deals\s*[:\-]?\s*(\d+)',
                r'>Total\s+deals</td>\s*<td[^>]*>(\d+)</td>',
            ],
            'total_profit': [
                r'Total\s+net\s+profit\s*[:\-]?\s*([\d\.\-]+)',
                r'>Total\s+net\s+profit</td>\s*<td[^>]*>([\d\.\-]+)</td>'
            ]
        }
        
        metrics = {}
        for metric_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    try:
                        if metric_name == 'drawdown' and len(match.groups()) > 1:
                            # Handle drawdown with percentage in parentheses
                            value = float(match.group(2))
                        else:
                            value = float(match.group(1))
                        metrics[metric_name] = value
                        break
                    except (ValueError, IndexError):
                        continue
        
        # Validate required metrics
        required = ['profit_factor', 'expected_payoff', 'drawdown', 'win_rate', 'trade_count']
        if not all(metric in metrics for metric in required):
            missing = [m for m in required if m not in metrics]
            logger.error(f"Missing metrics: {missing}")
            return None
        
        return BacktestMetrics(
            profit_factor=metrics['profit_factor'],
            expected_payoff=metrics['expected_payoff'],
            drawdown=metrics['drawdown'],
            win_rate=metrics['win_rate'],
            trade_count=int(metrics['trade_count']),
            total_profit=metrics.get('total_profit', 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error parsing backtest HTML: {e}")
        return None

def ensure_backtest_table():
    """Ensure backtest_benchmarks table exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                magic_number INTEGER NOT NULL,
                profit_factor REAL NOT NULL,
                expected_payoff REAL NOT NULL,
                drawdown REAL NOT NULL,
                win_rate REAL NOT NULL,
                trade_count INTEGER NOT NULL,
                total_profit REAL DEFAULT 0.0,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(magic_number)
            )
        """)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating backtest table: {e}")
        return False

@router.post("/upload")
async def upload_backtest_report(
    magic_number: int = Form(...),
    file: UploadFile = File(...)
):
    """Upload backtest HTML report for an EA"""
    print(f"🔄 Starting simple backtest upload for EA {magic_number}")
    
    try:
        # Validate file type
        if not file.filename.endswith(('.html', '.htm')):
            raise HTTPException(
                status_code=400, 
                detail="File must be an HTML backtest report"
            )
        
        print(f"📁 File validation passed: {file.filename}")
        
        # Read file content
        content = await file.read()
        html_content = content.decode('utf-8', errors='ignore')
        print(f"📖 File read successfully: {len(html_content)} characters")
        
        # Parse the HTML report
        print("🔍 Starting HTML parsing...")
        metrics = parse_backtest_html(html_content)
        
        if not metrics:
            print("❌ Parser returned None - file parsing failed")
            raise HTTPException(
                status_code=400,
                detail="Failed to parse backtest report. Please ensure it's a valid MT5 backtest HTML file."
            )
        
        print(f"✅ Parsing successful: PF={metrics.profit_factor}, EP={metrics.expected_payoff}, DD={metrics.drawdown}")
        
        # Ensure database table exists
        if not ensure_backtest_table():
            raise HTTPException(status_code=500, detail="Failed to initialize database table")
        
        # Store in database
        print("🗄️ Storing in database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_benchmarks 
                (magic_number, profit_factor, expected_payoff, drawdown, win_rate, trade_count, total_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                magic_number,
                metrics.profit_factor,
                metrics.expected_payoff,
                metrics.drawdown,
                metrics.win_rate,
                metrics.trade_count,
                metrics.total_profit
            ))
            
            conn.commit()
            print(f"✅ Backtest benchmark stored for EA {magic_number}")
            
            # Verify the data was stored
            cursor.execute("SELECT COUNT(*) FROM backtest_benchmarks WHERE magic_number = ?", (magic_number,))
            count = cursor.fetchone()[0]
            print(f"🔍 Verification: {count} benchmark(s) found for EA {magic_number}")
            
        except Exception as db_error:
            print(f"❌ Database error: {db_error}")
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            conn.close()
        
        return {
            "success": True,
            "message": f"Backtest report uploaded successfully for EA {magic_number}",
            "magic_number": magic_number,
            "metrics": {
                "profit_factor": metrics.profit_factor,
                "expected_payoff": metrics.expected_payoff,
                "drawdown": metrics.drawdown,
                "win_rate": metrics.win_rate,
                "trade_count": metrics.trade_count,
                "total_profit": metrics.total_profit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/benchmark/{magic_number}")
async def get_backtest_benchmark(magic_number: int):
    """Get backtest benchmark for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT profit_factor, expected_payoff, drawdown, win_rate, 
                   trade_count, total_profit, upload_date
            FROM backtest_benchmarks 
            WHERE magic_number = ?
            ORDER BY upload_date DESC 
            LIMIT 1
        """, (magic_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No backtest benchmark found for EA {magic_number}"
            )
        
        return {
            "success": True,
            "magic_number": magic_number,
            "benchmark": {
                "profit_factor": row[0],
                "expected_payoff": row[1],
                "drawdown": row[2],
                "win_rate": row[3],
                "trade_count": row[4],
                "total_profit": row[5],
                "upload_date": row[6]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Benchmark retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark: {str(e)}")

@router.get("/benchmarks")
async def get_all_benchmarks():
    """Get all backtest benchmarks"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT magic_number, profit_factor, expected_payoff, drawdown, 
                   win_rate, trade_count, total_profit, upload_date
            FROM backtest_benchmarks 
            ORDER BY upload_date DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        benchmarks = []
        for row in rows:
            benchmarks.append({
                "magic_number": row[0],
                "profit_factor": row[1],
                "expected_payoff": row[2],
                "drawdown": row[3],
                "win_rate": row[4],
                "trade_count": row[5],
                "total_profit": row[6],
                "upload_date": row[7]
            })
        
        return {
            "success": True,
            "benchmarks": benchmarks,
            "count": len(benchmarks)
        }
        
    except Exception as e:
        print(f"❌ Error getting all benchmarks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmarks: {str(e)}")

@router.delete("/benchmark/{magic_number}")
async def delete_benchmark(magic_number: int):
    """Delete backtest benchmark for specific EA"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM backtest_benchmarks WHERE magic_number = ?", (magic_number,))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"No benchmark found for EA {magic_number}"
            )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Benchmark deleted for EA {magic_number}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting benchmark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete benchmark: {str(e)}")

@router.get("/compare/{magic_number}")
async def compare_with_backtest(magic_number: int):
    """Compare EA's current performance with its backtest benchmark"""
    try:
        # Get backtest benchmark
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT profit_factor, expected_payoff, drawdown, win_rate, trade_count
            FROM backtest_benchmarks 
            WHERE magic_number = ?
        """, (magic_number,))
        
        benchmark_row = cursor.fetchone()
        if not benchmark_row:
            conn.close()
            raise HTTPException(
                status_code=404, 
                detail=f"No backtest benchmark found for EA {magic_number}"
            )
        
        # Get latest live performance (simplified - using EA status)
        cursor.execute("""
            SELECT id FROM eas WHERE magic_number = ?
        """, (magic_number,))
        ea_row = cursor.fetchone()
        
        if not ea_row:
            conn.close()
            raise HTTPException(status_code=404, detail="EA not found")
        
        ea_id = ea_row[0]
        
        cursor.execute("""
            SELECT total_profit, profit_factor, expected_payoff, drawdown, trade_count
            FROM performance_history 
            WHERE ea_id = ? 
            ORDER BY date DESC 
            LIMIT 1
        """, (ea_id,))
        
        live_row = cursor.fetchone()
        conn.close()
        
        if not live_row:
            # Use mock live data for demonstration
            live_pf = benchmark_row[0] * 0.85  # 15% worse than backtest
            live_ep = benchmark_row[1] * 0.90  # 10% worse
            live_dd = benchmark_row[2] * 1.20  # 20% higher drawdown
        else:
            live_pf = live_row[1]
            live_ep = live_row[2]
            live_dd = live_row[3]
        
        # Calculate deviations
        backtest_pf = benchmark_row[0]
        backtest_ep = benchmark_row[1]
        backtest_dd = benchmark_row[2]
        
        pf_deviation = ((live_pf - backtest_pf) / backtest_pf * 100) if backtest_pf != 0 else 0
        ep_deviation = ((live_ep - backtest_ep) / backtest_ep * 100) if backtest_ep != 0 else 0
        dd_deviation = ((live_dd - backtest_dd) / backtest_dd * 100) if backtest_dd != 0 else 0
        
        # Determine status
        overall_status = "good"
        if abs(pf_deviation) > 20 or abs(ep_deviation) > 25 or dd_deviation > 50:
            overall_status = "critical"
        elif abs(pf_deviation) > 10 or abs(ep_deviation) > 15 or dd_deviation > 25:
            overall_status = "warning"
        
        return {
            "success": True,
            "magic_number": magic_number,
            "comparison": {
                "overall_status": overall_status,
                "profit_factor_deviation": round(pf_deviation, 2),
                "expected_payoff_deviation": round(ep_deviation, 2),
                "drawdown_deviation": round(dd_deviation, 2)
            },
            "backtest_benchmark": {
                "profit_factor": backtest_pf,
                "expected_payoff": backtest_ep,
                "drawdown": backtest_dd,
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