"""
Test configuration and shared fixtures
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import json
import sqlite3

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import your application modules
import sys
sys.path.append('..')

from database.connection import get_db_session
from models.base import Base
from models.ea import EA, EAStatus
from models.performance import PerformanceHistory, BacktestBenchmark
from models.trade import Trade
from models.news import NewsEvent
from models.command import Command
from models.ea_tag import EATag
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    # Create in-memory database for faster tests
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield engine, TestingSessionLocal, str(db_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_session(temp_db):
    """Create a database session for testing"""
    engine, TestingSessionLocal, db_path = temp_db
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(temp_db):
    """Create a test client for FastAPI"""
    engine, TestingSessionLocal, db_path = temp_db
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override the database dependency
    from database.connection import get_db_session
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_ea(db_session):
    """Create a sample EA for testing"""
    ea = EA(
        magic_number=12345,
        symbol="EURUSD",
        strategy_tag="Test_Strategy_v1",
        risk_config=1.0,
        status="active"
    )
    db_session.add(ea)
    db_session.commit()
    db_session.refresh(ea)
    return ea


@pytest.fixture
def sample_ea_status(db_session, sample_ea):
    """Create sample EA status for testing"""
    status = EAStatus(
        ea_id=sample_ea.id,
        current_profit=150.50,
        open_positions=2,
        sl_value=1.0850,
        tp_value=1.0950,
        trailing_active=True,
        module_status=json.dumps({
            "BB": "expansion",
            "RSI": "oversold", 
            "MA": "bullish"
        })
    )
    db_session.add(status)
    db_session.commit()
    db_session.refresh(status)
    return status


@pytest.fixture
def sample_performance_history(db_session, sample_ea):
    """Create sample performance history for testing"""
    performance = PerformanceHistory(
        ea_id=sample_ea.id,
        total_profit=1250.75,
        profit_factor=1.65,
        expected_payoff=25.50,
        drawdown=5.2,
        z_score=2.1,
        trade_count=49
    )
    db_session.add(performance)
    db_session.commit()
    db_session.refresh(performance)
    return performance


@pytest.fixture
def sample_backtest_benchmark(db_session, sample_ea):
    """Create sample backtest benchmark for testing"""
    benchmark = BacktestBenchmark(
        ea_id=sample_ea.id,
        profit_factor=1.85,
        expected_payoff=28.75,
        drawdown=3.8,
        win_rate=62.5,
        trade_count=200
    )
    db_session.add(benchmark)
    db_session.commit()
    db_session.refresh(benchmark)
    return benchmark


@pytest.fixture
def sample_trade(db_session, sample_ea):
    """Create sample trade for testing"""
    trade = Trade(
        ea_id=sample_ea.id,
        ticket=123456789,
        symbol="EURUSD",
        trade_type="buy",
        volume=1.0,
        open_price=1.0900,
        close_price=1.0925,
        sl=1.0850,
        tp=1.0950,
        open_time=datetime.utcnow() - timedelta(hours=2),
        close_time=datetime.utcnow(),
        profit=25.0,
        commission=-7.0,
        swap=-2.0,
        comment="Test trade"
    )
    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)
    return trade


@pytest.fixture
def sample_news_event(db_session):
    """Create sample news event for testing"""
    event = NewsEvent(
        currency="USD",
        event_name="Non-Farm Payrolls",
        impact_level="high",
        event_time=datetime.utcnow() + timedelta(hours=2),
        description="Monthly employment data release"
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sample_command(db_session, sample_ea):
    """Create sample command for testing"""
    command = Command(
        ea_id=sample_ea.id,
        command_type="pause",
        parameters=json.dumps({"reason": "news_event"}),
        status="pending",
        execution_time=datetime.utcnow() + timedelta(minutes=5)
    )
    db_session.add(command)
    db_session.commit()
    db_session.refresh(command)
    return command


@pytest.fixture
def mt5_mock_data():
    """Mock MT5 data for testing"""
    return {
        "COC_EA_12345_DATA": json.dumps({
            "magic_number": 12345,
            "symbol": "EURUSD",
            "strategy_tag": "Test_Strategy_v1",
            "current_profit": 150.50,
            "open_positions": 2,
            "trade_status": "active",
            "sl_value": 1.0850,
            "tp_value": 1.0950,
            "trailing_active": True,
            "module_status": {
                "BB": "expansion",
                "RSI": "oversold",
                "MA": "bullish"
            },
            "performance_metrics": {
                "profit_factor": 1.65,
                "expected_payoff": 25.50,
                "drawdown": 5.2,
                "z_score": 2.1,
                "trade_count": 49
            },
            "last_trades": [
                "[BUY] EURUSD 1.0 @ 1.0900 → 1.0925 (+25.0)",
                "[SELL] EURUSD 1.0 @ 1.0880 → 1.0860 (+20.0)"
            ],
            "coc_override": False,
            "last_update": datetime.utcnow().isoformat()
        })
    }


@pytest.fixture
def mock_news_api_response():
    """Mock news API response for testing"""
    return [
        {
            "currency": "USD",
            "event": "Non-Farm Payrolls",
            "impact": "High",
            "time": "2024-01-05T13:30:00Z",
            "description": "Monthly employment data"
        },
        {
            "currency": "EUR", 
            "event": "ECB Interest Rate Decision",
            "impact": "High",
            "time": "2024-01-05T12:45:00Z",
            "description": "Central bank monetary policy"
        }
    ]


@pytest.fixture
def sample_backtest_html():
    """Sample MT5 backtest HTML for testing"""
    return '''
    <html>
    <head><title>Strategy Tester Report</title></head>
    <body>
    <table>
        <tr><td>Total net profit</td><td>1234.56</td></tr>
        <tr><td>Profit factor</td><td>1.85</td></tr>
        <tr><td>Expected payoff</td><td>28.75</td></tr>
        <tr><td>Maximal drawdown</td><td>123.45 (3.80%)</td></tr>
        <tr><td>Total trades</td><td>200</td></tr>
        <tr><td>Winning trades (% of total)</td><td>125 (62.50%)</td></tr>
    </table>
    </body>
    </html>
    '''


@pytest.fixture
def websocket_mock():
    """Mock WebSocket connection for testing"""
    mock = Mock()
    mock.send = Mock()
    mock.recv = Mock()
    mock.close = Mock()
    return mock


@pytest.fixture
def temp_mt5_dirs():
    """Create temporary MT5 directories for testing"""
    temp_dir = tempfile.mkdtemp()
    
    globals_dir = Path(temp_dir) / "mt5_globals"
    fallback_dir = Path(temp_dir) / "mt5_fallback"
    
    globals_dir.mkdir()
    fallback_dir.mkdir()
    (fallback_dir / "commands").mkdir()
    (fallback_dir / "ea_data").mkdir()
    (fallback_dir / "heartbeat").mkdir()
    
    yield {
        "temp_dir": temp_dir,
        "globals_dir": str(globals_dir),
        "fallback_dir": str(fallback_dir)
    }
    
    shutil.rmtree(temp_dir)


# Test data generators
class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def create_multiple_eas(db_session, count=5):
        """Create multiple EAs for testing"""
        eas = []
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF"]
        strategies = ["Scalper_v1", "Swing_v2", "Breakout_v3", "Mean_Reversion_v1", "Momentum_v2"]
        
        for i in range(count):
            ea = EA(
                magic_number=10000 + i,
                symbol=symbols[i % len(symbols)],
                strategy_tag=strategies[i % len(strategies)],
                risk_config=1.0 + (i * 0.1),
                status="active" if i % 2 == 0 else "paused"
            )
            eas.append(ea)
            db_session.add(ea)
        
        db_session.commit()
        return eas
    
    @staticmethod
    def create_performance_data(db_session, ea, days=30):
        """Create historical performance data"""
        performances = []
        base_date = datetime.utcnow().date()
        
        for i in range(days):
            date = base_date - timedelta(days=i)
            performance = PerformanceHistory(
                ea_id=ea.id,
                date=date,
                total_profit=1000 + (i * 50),
                profit_factor=1.5 + (i * 0.01),
                expected_payoff=20 + (i * 0.5),
                drawdown=3.0 + (i * 0.1),
                z_score=2.0 + (i * 0.05),
                trade_count=i + 10
            )
            performances.append(performance)
            db_session.add(performance)
        
        db_session.commit()
        return performances


@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory
