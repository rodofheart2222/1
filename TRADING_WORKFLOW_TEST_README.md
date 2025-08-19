# MT5 Trading Workflow Test System

This comprehensive test system validates the complete MT5 trading workflow from dashboard to MT5 execution, covering all the scenarios you specified.

## 🎯 Test Coverage

### 1. Connect & Heartbeat
- ✅ Dashboard lists EA instance (EX BOC V24) with Magic#, Symbol, TF
- ✅ Status shows "Connected" with last heartbeat < 2s
- ✅ WebSocket connection and authentication
- ✅ Real-time status updates

### 2. Open Orders (OCO)
- ✅ Send Buy Limit and Sell Stop from dashboard
- ✅ MT5 shows both pending orders in Trade tab
- ✅ Prices match between dashboard and MT5
- ✅ Journal prints `[ENTRY]` messages

### 3. Modify & Cancel
- ✅ Change risk% and pending prices from dashboard
- ✅ MT5 updates within 500ms p95
- ✅ Cancel pending orders from dashboard
- ✅ Orders disappear in MT5 with `[CANCEL]` logged

### 4. Force Fill
- ✅ Nudge price to trigger pending order fill
- ✅ MT5 shows position after fill
- ✅ Dashboard shows Entry/SL/TP/Profile
- ✅ Journal logs `[SL] clamp`, `[TP] placed`, `[RR]` messages

### 5. Close from Dashboard
- ✅ Close position from dashboard
- ✅ MT5 closes position
- ✅ P&L appears on both sides within 1s

### 6. Restart Robustness
- ✅ Kill MT5 and dashboard, restart both
- ✅ Existing pending/position reloads with correct state
- ✅ System recovery validation

### 7. Latency & Logs
- ✅ Round-trip timing (dashboard→MT5→dashboard)
- ✅ Export rolling CSV/JSON logs
- ✅ Tagged entries: `[ENTRY]` `[SL]` `[TP]` `[RR]` `[CANCEL]`

## 🚀 Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install -r test_requirements.txt

# Ensure your backend server is ready
cd backend
pip install -r requirements.txt
```

### Run Complete Test Suite
```bash
# Run all tests with default settings
python run_complete_test_system.py

# Run with custom EA and symbol
python run_complete_test_system.py --ea-magic 54321 --symbol GBPUSD

# Run with custom host
python run_complete_test_system.py --host 192.168.1.100
```

### Run Individual Components

#### 1. Start Backend Server Only
```bash
python backend/start_complete_server.py --host 127.0.0.1 --port 80 --ws-port 8765
```

#### 2. Start EA Simulator Only
```bash
python simulate_ea_responses.py --magic 12345 --symbol EURUSD --host 127.0.0.1
```

#### 3. Run Tests Only (requires server + simulator running)
```bash
python test_complete_trading_workflow.py --ea-magic 12345 --symbol EURUSD --host 127.0.0.1
```

## 📊 Test Output

### Console Output
The test system provides real-time feedback with emojis and structured logging:

```
🚀 Starting Complete MT5 Trading Workflow Tests
EA Magic: 12345, Symbol: EURUSD, Host: 127.0.0.1

✅ Connect & Heartbeat: PASS (1234.56ms) - EA 12345 connected, Status=Connected, heartbeat < 2s
✅ Open Orders (OCO): PASS (2345.67ms) - Buy Limit @ 1.0827 and Sell Stop @ 1.0867 placed successfully
✅ Modify & Cancel: PASS (456.78ms) - Modified orders in 234.5ms, cancelled 2 orders
✅ Force Fill: PASS (3456.78ms) - Order filled at 1.0827, SL/TP placed, position shows in MT5
✅ Close Position: PASS (567.89ms) - Position closed in 123.4ms, P&L updated on both sides
✅ Restart Robustness: PASS (4567.89ms) - System recovered successfully, EA state preserved
✅ Latency & Logs: PASS (678.90ms) - Round-trip avg: 45.6ms, Logs exported to CSV/JSON

🏁 TRADING WORKFLOW TEST SUMMARY
Total Tests: 7
✅ Passed: 7
❌ Failed: 0
📊 Success Rate: 100.0%
⏱️ Total Duration: 12345.67ms
🔄 Avg Operation Latency: 45.67ms
```

### Generated Files

#### 1. CSV Log Export
`trading_workflow_log_YYYYMMDD_HHMMSS.csv`
```csv
timestamp,tag,operation,status,duration_ms,latency_ms,message,details
2024-01-15T10:30:00,[ENTRY],place_order,success,,234.5,Buy Limit placed,Order details...
2024-01-15T10:30:01,[SL],sl_clamp,success,,12.3,Stop Loss activated,SL details...
2024-01-15T10:30:02,[TP],tp_placed,success,,15.7,Take Profit set,TP details...
```

#### 2. JSON Log Export
`trading_workflow_log_YYYYMMDD_HHMMSS.json`
```json
{
  "test_session": {
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T10:35:00",
    "ea_magic": 12345,
    "test_symbol": "EURUSD"
  },
  "latency_statistics": {
    "round_trip_avg_ms": 45.67,
    "round_trip_min_ms": 23.45,
    "round_trip_max_ms": 89.12,
    "total_operations": 25
  },
  "test_results": [...],
  "detailed_logs": [...]
}
```

#### 3. Final Test Report
`final_test_report_YYYYMMDD_HHMMSS.json`
```json
{
  "system_config": {
    "ea_magic": 12345,
    "symbol": "EURUSD",
    "host": "127.0.0.1"
  },
  "results_summary": {
    "total_tests": 7,
    "passed": 7,
    "failed": 0,
    "success_rate": 100.0
  },
  "recommendations": [...]
}
```

## 🔧 Configuration Options

### Command Line Arguments

#### Complete Test System
```bash
python run_complete_test_system.py \
  --ea-magic 12345 \          # EA Magic Number
  --symbol EURUSD \           # Trading Symbol
  --host 127.0.0.1 \    # Server Host
  --no-report                 # Skip final report generation
```

#### Individual Test Runner
```bash
python test_complete_trading_workflow.py \
  --ea-magic 12345 \          # EA Magic Number
  --symbol EURUSD \           # Trading Symbol
  --host 127.0.0.1 \    # Server Host
  --port 80 \                 # API Port
  --ws-port 8765              # WebSocket Port
```

#### EA Simulator
```bash
python simulate_ea_responses.py \
  --magic 12345 \             # EA Magic Number
  --symbol EURUSD \           # Trading Symbol
  --host 127.0.0.1 \    # Server Host
  --port 80                   # Server Port
```

### Environment Variables
```bash
# Optional environment configuration
export MT5_TEST_HOST=127.0.0.1
export MT5_TEST_PORT=80
export MT5_TEST_WS_PORT=8765
export MT5_TEST_EA_MAGIC=12345
export MT5_TEST_SYMBOL=EURUSD
```

## 📈 Performance Benchmarks

### Latency Targets
- **Order Placement**: < 200ms p95
- **Order Modification**: < 500ms p95
- **Order Cancellation**: < 300ms p95
- **Position Close**: < 1000ms p95
- **Round-trip Communication**: < 100ms average
- **Heartbeat Response**: < 50ms

### Success Rate Targets
- **Overall Test Success**: > 95%
- **Command Acknowledgment**: > 99%
- **WebSocket Connectivity**: > 99.9%
- **State Persistence**: 100%

## 🛠️ Troubleshooting

### Common Issues

#### 1. Connection Refused
```
Error: Connection refused to 127.0.0.1:80
```
**Solution**: Ensure backend server is running:
```bash
python backend/start_complete_server.py
```

#### 2. WebSocket Connection Failed
```
Error: WebSocket connection failed
```
**Solution**: Check WebSocket server is running on port 8765:
```bash
netstat -an | grep 8765
```

#### 3. EA Not Found
```
Error: EA 12345 not found
```
**Solution**: Ensure EA simulator is running:
```bash
python simulate_ea_responses.py --magic 12345
```

#### 4. High Latency
```
Warning: Average latency 500ms exceeds target
```
**Solution**: 
- Check network connectivity
- Reduce server load
- Optimize database queries

### Debug Mode
Enable detailed logging:
```bash
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
python test_complete_trading_workflow.py --ea-magic 12345
```

### Manual Testing
Test individual API endpoints:
```bash
# Check EA status
curl http://127.0.0.1:80/api/ea/status/12345

# Send command
curl -X POST http://127.0.0.1:80/api/ea/command/12345 \
  -H "Content-Type: application/json" \
  -d '{"command":"PING","parameters":{}}'

# Check system health
curl http://127.0.0.1:80/health
```

## 🔍 Test Scenarios Detail

### Scenario 1: Connect & Heartbeat
1. **API Health Check**: Verify backend is responsive
2. **WebSocket Connection**: Establish real-time communication
3. **EA Registration**: Register EA with magic number and symbol
4. **Status Verification**: Confirm EA appears in dashboard
5. **Heartbeat Test**: Verify < 2s response time

### Scenario 2: Open Orders (OCO)
1. **Get Current Price**: Fetch market price for symbol
2. **Calculate Order Prices**: Set Buy Limit below, Sell Stop above market
3. **Place Buy Limit**: Send order with SL/TP
4. **Place Sell Stop**: Send complementary order
5. **Verify Acknowledgment**: Confirm both orders received
6. **Check Journal**: Verify `[ENTRY]` messages logged

### Scenario 3: Modify & Cancel
1. **Modify Order**: Change risk% and price levels
2. **Measure Latency**: Ensure < 500ms p95 response
3. **Cancel Orders**: Remove all pending orders
4. **Verify Removal**: Confirm orders disappeared
5. **Check Journal**: Verify `[CANCEL]` messages logged

### Scenario 4: Force Fill
1. **Place Near-Market Order**: Order likely to fill quickly
2. **Monitor for Fill**: Watch for position creation
3. **Verify SL/TP**: Confirm stop loss and take profit set
4. **Check Journal**: Verify `[SL] clamp`, `[TP] placed`, `[RR]` messages
5. **Position Tracking**: Confirm position shows in dashboard

### Scenario 5: Close Position
1. **Identify Open Position**: Find position to close
2. **Send Close Command**: Request position closure
3. **Measure Close Time**: Ensure < 1s execution
4. **Verify P&L**: Confirm profit/loss calculated
5. **Check Both Sides**: Verify dashboard and MT5 sync

### Scenario 6: Restart Robustness
1. **Record Pre-State**: Document current positions/orders
2. **Simulate Restart**: Disconnect and reconnect systems
3. **Verify Recovery**: Confirm state preservation
4. **Test Functionality**: Ensure commands still work
5. **State Comparison**: Validate data integrity

### Scenario 7: Latency & Logs
1. **Round-Trip Tests**: Measure dashboard→MT5→dashboard timing
2. **Statistical Analysis**: Calculate avg/min/max latencies
3. **Log Generation**: Create tagged CSV/JSON exports
4. **Performance Report**: Generate latency statistics
5. **Export Validation**: Verify log file integrity

## 📋 Checklist for Production

### Pre-Deployment
- [ ] All tests pass with > 95% success rate
- [ ] Average latency < 100ms
- [ ] WebSocket stability > 99.9%
- [ ] Database integrity verified
- [ ] Error handling tested
- [ ] Load testing completed

### Monitoring Setup
- [ ] Latency monitoring configured
- [ ] Error rate alerts set up
- [ ] Performance dashboards created
- [ ] Log aggregation enabled
- [ ] Health check endpoints monitored

### Documentation
- [ ] API documentation updated
- [ ] Deployment guide created
- [ ] Troubleshooting guide available
- [ ] Performance benchmarks documented
- [ ] Recovery procedures defined

## 🤝 Contributing

### Adding New Tests
1. Create test function in `test_complete_trading_workflow.py`
2. Add to `test_functions` list in `run_all_tests()`
3. Update documentation
4. Ensure proper error handling and logging

### Extending EA Simulator
1. Add new command handler in `simulate_ea_responses.py`
2. Update `_process_command()` method
3. Add appropriate logging with tags
4. Test command acknowledgment flow

### Performance Optimization
1. Profile bottlenecks using `cProfile`
2. Optimize database queries
3. Implement connection pooling
4. Add caching where appropriate
5. Monitor memory usage

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review log files for error details
3. Test individual components separately
4. Verify network connectivity and ports
5. Check system resources and dependencies

## 🔄 Version History

- **v1.0**: Initial complete workflow test system
- **v1.1**: Added latency monitoring and CSV export
- **v1.2**: Enhanced error handling and recovery testing
- **v1.3**: Added performance benchmarks and recommendations

---

**Happy Testing! 🚀**