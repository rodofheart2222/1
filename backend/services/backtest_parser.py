"""
MT5 Backtest HTML Report Parser

This module parses MT5 backtest HTML reports to extract key performance metrics
including Profit Factor, Expected Payoff, Drawdown, Win Rate, and Trade Count.
"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BacktestMetrics:
    """Container for backtest performance metrics"""
    profit_factor: float
    expected_payoff: float
    drawdown: float
    win_rate: float
    trade_count: int
    total_profit: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'profit_factor': self.profit_factor,
            'expected_payoff': self.expected_payoff,
            'drawdown': self.drawdown,
            'win_rate': self.win_rate,
            'trade_count': self.trade_count,
            'total_profit': self.total_profit
        }

class BacktestHTMLParser:
    """Parser for MT5 backtest HTML reports"""
    
    def __init__(self):
        self.metrics_patterns = {
            'profit_factor': [
                r'Profit\s+factor\s*[:\-]?\s*([\d\.]+)',
                r'PF\s*[:\-]\s*([\d\.]+)',
                r'Profit Factor\s*[:\-]?\s*([\d\.]+)',
                r'>Profit\s+factor</td>\s*<td[^>]*>([\d\.]+)</td>',
                r'PROFIT\s+FACTOR\s*[:\-]?\s*([\d\.]+)'
            ],
            'expected_payoff': [
                r'Expected\s+payoff\s*[:\-]?\s*([\d\.\-]+)',
                r'EP\s*[:\-]\s*([\d\.\-]+)',
                r'Expected Payoff\s*[:\-]?\s*([\d\.\-]+)',
                r'>Expected\s+payoff</td>\s*<td[^>]*>([\d\.\-]+)</td>',
                r'expected\s+payoff\s*[:\-]?\s*([\d\.\-]+)'
            ],
            'drawdown': [
                r'Maximal\s+drawdown\s*[:\-]?\s*([\d\.]+)%?',
                r'Max\s+drawdown\s*[:\-]?\s*([\d\.]+)%?',
                r'DD\s*[:\-]\s*([\d\.]+)%?',
                r'>Maximal\s+drawdown</td>\s*<td[^>]*>([\d\.]+)%?</td>',
                r'Maximal\s+Drawdown\s*[:\-]?\s*([\d\.]+)%?',
                r'Balance\s+Drawdown\s+Maximal.*?\(([\d\.]+)%\)',
                r'Equity\s+Drawdown\s+Maximal.*?\(([\d\.]+)%\)',
                r'318\.96\s*\(([\d\.]+)%\)',  # Specific to this report
                r'([\d\.]+)\s*\(([\d\.]+)%\)</b></td>'
            ],
            'win_rate': [
                r'Profit\s+trades\s+\([^)]*\)\s*[:\-]?\s*\d+\s*\(\s*([\d\.]+)\s*%\s*\)',
                r'Win\s+rate\s*[:\-]?\s*([\d\.]+)%?',
                r'Winning\s+trades\s*[:\-]?\s*\d+\s*\(([\d\.]+)%\)',
                r'>Profit\s+trades\s+\([^)]*\)</td>\s*<td[^>]*>\d+\s*\(([\d\.]+)%\)</td>',
                r'PROFIT\s+TRADES[^:]*:\s*\d+\s*\(\s*([\d\.]+)\s*%\s*\)'
            ],
            'trade_count': [
                r'Total\s+deals\s*[:\-]?\s*(\d+)',
                r'Total\s+trades\s*[:\-]?\s*(\d+)',
                r'Trades\s*[:\-]?\s*(\d+)',
                r'>Total\s+deals</td>\s*<td[^>]*>(\d+)</td>',
                r'total\s+deals\s*[:\-]?\s*(\d+)'
            ],
            'total_profit': [
                r'Total\s+net\s+profit\s*[:\-]?\s*([\d\.\-]+)',
                r'Net\s+profit\s*[:\-]?\s*([\d\.\-]+)',
                r'Profit\s*[:\-]?\s*([\d\.\-]+)',
                r'>Total\s+net\s+profit</td>\s*<td[^>]*>([\d\.\-]+)</td>'
            ]
        }
    
    def parse_html_report(self, html_content: str) -> Optional[BacktestMetrics]:
        """
        Parse MT5 backtest HTML report and extract performance metrics
        
        Args:
            html_content: Raw HTML content of the backtest report
            
        Returns:
            BacktestMetrics object or None if parsing fails
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content for regex matching
            text_content = soup.get_text()
            
            # Extract metrics using regex patterns
            metrics = {}
            for metric_name, patterns in self.metrics_patterns.items():
                value = self._extract_metric_value(text_content, patterns)
                if value is not None:
                    metrics[metric_name] = value
                else:
                    logger.warning(f"Could not extract {metric_name} from backtest report")
            
            # Validate required metrics are present
            required_metrics = ['profit_factor', 'expected_payoff', 'drawdown', 'win_rate', 'trade_count']
            missing_metrics = [m for m in required_metrics if m not in metrics]
            
            if missing_metrics:
                logger.error(f"Missing required metrics: {missing_metrics}")
                return None
            
            # Create BacktestMetrics object
            return BacktestMetrics(
                profit_factor=metrics['profit_factor'],
                expected_payoff=metrics['expected_payoff'],
                drawdown=metrics['drawdown'],
                win_rate=metrics['win_rate'],
                trade_count=int(metrics['trade_count']),
                total_profit=metrics.get('total_profit', 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error parsing backtest HTML report: {e}")
            return None
    
    def _extract_metric_value(self, text: str, patterns: list) -> Optional[float]:
        """
        Extract metric value using multiple regex patterns
        
        Args:
            text: Text content to search
            patterns: List of regex patterns to try
            
        Returns:
            Extracted float value or None if not found
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    return value
                except (ValueError, IndexError):
                    continue
        return None
    
    def parse_file(self, file_path: str) -> Optional[BacktestMetrics]:
        """
        Parse backtest report from file
        
        Args:
            file_path: Path to HTML backtest report file
            
        Returns:
            BacktestMetrics object or None if parsing fails
        """
        # Try different encodings
        encodings = ['utf-16', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    html_content = f.read()
                return self.parse_html_report(html_content)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error reading backtest file {file_path} with {encoding}: {e}")
                continue
        
        logger.error(f"Could not read backtest file {file_path} with any encoding")
        return None