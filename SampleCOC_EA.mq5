//+------------------------------------------------------------------+
//|                                               SampleCOC_EA.mq5  |
//|                             Sample EA for MT5 COC Dashboard     |
//|                           Connects to backend via HTTP API      |
//+------------------------------------------------------------------+
#property copyright "MT5 COC Dashboard"
#property link      "http://localhost:80"
#property version   "1.00"
#property strict

//--- Input parameters
input int    Magic_Number = 12345;           // Unique Magic Number for this EA
input string Strategy_Tag = "MACD_TREND";    // Strategy identification tag
input double Risk_Percent_Input = 1.0;       // Risk percentage per trade
input double Fixed_Lot_Size = 0.01;          // Fixed lot size (when enabled)
input bool   Use_Fixed_Lot = false;          // Use fixed lot size instead of risk calculation
input int    Status_Update_Interval = 30;    // Status update interval in seconds
input int    Command_Check_Interval = 10;    // Command check interval in seconds
input string Backend_URL = "http://127.0.0.1:80"; // Backend API URL

//--- Global variables
datetime last_status_update = 0;
datetime last_command_check = 0;
bool ea_initialized = false;
bool coc_override = false;
bool is_paused = false;
double Risk_Percent = 1.0;  // Modifiable risk percentage
double Dynamic_Fixed_Lot_Size = 0.01;  // Runtime modifiable lot size
bool Dynamic_Use_Fixed_Lot = false;    // Runtime modifiable fixed lot flag

//--- Trading control variables
int Max_Positions = 3;                 // Maximum concurrent positions
double Default_Stop_Loss = 50.0;       // Default stop loss in points
double Default_Take_Profit = 100.0;    // Default take profit in points

//--- EA Instance identification
string Instance_UUID = "";  // Unique identifier for this EA instance

//--- Trading variables
double current_profit = 0.0;
int open_positions = 0;
double sl_value = 0.0;
double tp_value = 0.0;
bool trailing_active = false;

//--- Performance tracking
double total_profit = 0.0;
int total_trades = 0;
double max_drawdown = 0.0;
double peak_equity = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🚀 Sample COC EA Starting - Magic Number: ", Magic_Number);
    Print("📡 Backend URL: ", Backend_URL);
    Print("🏷️ Strategy Tag: ", Strategy_Tag);
    
    // Initialize variables
    Risk_Percent = Risk_Percent_Input;  // Copy input to modifiable variable
    Dynamic_Fixed_Lot_Size = Fixed_Lot_Size;  // Copy input to modifiable variable
    Dynamic_Use_Fixed_Lot = Use_Fixed_Lot;    // Copy input to modifiable variable
    peak_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    
    // Generate unique instance UUID
    Instance_UUID = GenerateInstanceUUID();
    Print("🆔 Instance UUID: ", Instance_UUID);
    
    // Send initial registration to backend
    if(RegisterEAWithBackend())
    {
        ea_initialized = true;
        Print("✅ EA successfully registered with COC Dashboard");
    }
    else
    {
        Print("❌ Failed to register with COC Dashboard - continuing in standalone mode");
        ea_initialized = false;
    }
    
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Generate Instance UUID                                           |
//+------------------------------------------------------------------+
string GenerateInstanceUUID()
{
    // Generate pseudo-UUID using account info, symbol, magic number, and timestamp
    // Format: MAGIC-ACCOUNT-SYMBOL-TIMESTAMP-RANDOM
    long account = AccountInfoInteger(ACCOUNT_LOGIN);
    long timestamp = TimeCurrent();
    int random_val = MathRand();
    
    string uuid = IntegerToString(Magic_Number) + "-" + 
                  IntegerToString(account) + "-" + 
                  Symbol() + "-" + 
                  IntegerToString(timestamp) + "-" + 
                  IntegerToString(random_val);
    
    // Convert to uppercase hex-like format
    StringReplace(uuid, "-", "");
    if(StringLen(uuid) > 32) {
        uuid = StringSubstr(uuid, 0, 32);
    }
    
    // Add dashes in UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    string formatted_uuid = StringSubstr(uuid, 0, 8) + "-" +
                           StringSubstr(uuid, 8, 4) + "-" +
                           StringSubstr(uuid, 12, 4) + "-" +
                           StringSubstr(uuid, 16, 4) + "-" +
                           StringSubstr(uuid, 20, 12);
    
    return formatted_uuid;
}

//+------------------------------------------------------------------+
//| Get Timeframe String                                             |
//+------------------------------------------------------------------+
string GetTimeframeString()
{
    int period = Period();
    
    switch(period)
    {
        case PERIOD_M1:  return "M1";
        case PERIOD_M5:  return "M5";
        case PERIOD_M15: return "M15";
        case PERIOD_M30: return "M30";
        case PERIOD_H1:  return "H1";
        case PERIOD_H4:  return "H4";
        case PERIOD_D1:  return "D1";
        case PERIOD_W1:  return "W1";
        case PERIOD_MN1: return "MN1";
        default: return "M" + IntegerToString(period);
    }
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 Sample COC EA Stopping - Reason: ", reason);
    
    // Send final status update
    if(ea_initialized)
    {
        SendStatusUpdate();
    }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Update current performance metrics
    UpdatePerformanceMetrics();
    
    // Periodic status updates to backend (ALWAYS send, even when paused)
    if(ea_initialized && TimeCurrent() > last_status_update + Status_Update_Interval)
    {
        SendStatusUpdate();
        last_status_update = TimeCurrent();
    }
    
    // Check for commands from backend (ALWAYS check, even when paused - needed for resume)
    if(ea_initialized && TimeCurrent() > last_command_check + Command_Check_Interval)
    {
        CheckForCommands();
        last_command_check = TimeCurrent();
    }
    
    // Check if EA is paused by COC - skip trading logic only
    if(is_paused)
    {
        return; // Skip trading logic when paused, but still send updates and check commands
    }
    
    // Execute trading logic (if not overridden by COC)
    if(!coc_override)
    {
        ExecuteTradingLogic();
    }
}

//+------------------------------------------------------------------+
//| Register EA with Backend                                         |
//+------------------------------------------------------------------+
bool RegisterEAWithBackend()
{
    // Use query parameters for registration (MT5 compatible)
    string url = Backend_URL + "/api/ea/register";
    url += "?magic_number=" + IntegerToString(Magic_Number);
    url += "&symbol=" + Symbol();
    url += "&strategy_tag=" + Strategy_Tag;
    url += "&version=1.0";
    url += "&instance_uuid=" + Instance_UUID;
    
    // Add additional instance information
    url += "&account_number=" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
    url += "&broker=" + AccountInfoString(ACCOUNT_COMPANY);
    url += "&timeframe=" + GetTimeframeString();
    url += "&server_info=" + AccountInfoString(ACCOUNT_SERVER);
    
    Print("🔗 Attempting to connect to: ", url);
    Print("📋 Using Backend_URL: ", Backend_URL);
    Print("🆔 Instance UUID: ", Instance_UUID);
    
    // Empty headers for simple POST with query parameters
    string headers = "";
    
    uchar post[], result[];
    string result_headers;
    
    // Send empty POST body with all parameters in URL
    int res = WebRequest("POST", url, headers, 5000, post, result, result_headers);
    
    if(res == 200)
    {
        Print("✅ EA Registration successful");
        return true;
    }
    else
    {
        Print("❌ EA Registration failed with code: ", res);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Send Status Update to Backend                                   |
//+------------------------------------------------------------------+
bool SendStatusUpdate()
{
    string url = Backend_URL + "/api/ea/status";
    string headers = "Content-Type: application/json\r\n";
    
    // Update current metrics
    UpdatePerformanceMetrics();
    
    // Get recent trades
    string recent_trades = GetRecentTrades();
    
    // Create status JSON
    string json = "{";
    json += "\"instance_uuid\":\"" + Instance_UUID + "\",";
    json += "\"magic_number\":" + IntegerToString(Magic_Number) + ",";
    json += "\"symbol\":\"" + Symbol() + "\",";
    json += "\"strategy_tag\":\"" + Strategy_Tag + "\",";
    json += "\"current_profit\":" + DoubleToString(current_profit, 2) + ",";
    json += "\"open_positions\":" + IntegerToString(open_positions) + ",";
    json += "\"sl_value\":" + DoubleToString(sl_value, 5) + ",";
    json += "\"tp_value\":" + DoubleToString(tp_value, 5) + ",";
    json += "\"trailing_active\":" + (trailing_active ? "true" : "false") + ",";
    json += "\"module_status\":" + GetModuleStatus() + ",";
    json += "\"performance_metrics\":" + GetPerformanceMetrics() + ",";
    json += "\"last_trades\":" + recent_trades + ",";
    json += "\"coc_override\":" + (coc_override ? "true" : "false") + ",";
    json += "\"is_paused\":" + (is_paused ? "true" : "false") + ",";
    json += "\"risk_percent\":" + DoubleToString(Risk_Percent, 2) + ",";
    json += "\"use_fixed_lot\":" + (Dynamic_Use_Fixed_Lot ? "true" : "false") + ",";
    json += "\"fixed_lot_size\":" + DoubleToString(Dynamic_Fixed_Lot_Size, 2) + ",";
    json += "\"current_lot_size\":" + DoubleToString(CalculateLotSize(), 2) + ",";
    json += "\"max_positions\":" + IntegerToString(Max_Positions) + ",";
    json += "\"default_stop_loss\":" + DoubleToString(Default_Stop_Loss, 1) + ",";
    json += "\"default_take_profit\":" + DoubleToString(Default_Take_Profit, 1) + ",";
    json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
    json += "}";
    
    uchar post[], result[];
    StringToCharArray(json, post, 0, StringLen(json));
    
    string result_headers;
    int res = WebRequest("POST", url, headers, 5000, post, result, result_headers);
    
    if(res == 200)
    {
        Print("📊 Status update sent successfully");
        return true;
    }
    else
    {
        Print("❌ Failed to send status update. Response code: ", res);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Check for Commands from Backend                                 |
//+------------------------------------------------------------------+
void CheckForCommands()
{
    // Try both UUID-based and magic-number-based endpoints for maximum compatibility
    string uuid_url = Backend_URL + "/api/ea/commands/instance/" + Instance_UUID;
    string magic_url = Backend_URL + "/api/ea/commands/" + IntegerToString(Magic_Number);
    
    // Try UUID endpoint first
    uchar data[], result[];
    string result_headers;
    int res = WebRequest("GET", uuid_url, "", 5000, data, result, result_headers);
    
    if(res == 200)
    {
        string json_result = CharArrayToString(result);
        if(StringFind(json_result, "\"command\":null") < 0 && StringFind(json_result, "command\": null") < 0)
        {
            Print("📋 Received command via UUID endpoint");
            ProcessCommands(json_result);
            return;
        }
    }
    
    // No fallback to magic number endpoint - UUID-only for precise targeting
    // This prevents cross-EA interference when multiple EAs have same magic number
}

//+------------------------------------------------------------------+
//| Process Commands from Backend                                   |
//+------------------------------------------------------------------+
void ProcessCommands(string json_commands)
{
    Print("📋 Processing commands: ", json_commands);
    
    // Check if we have a valid command response
    if(StringFind(json_commands, "\"command\":null") >= 0 || StringFind(json_commands, "command\": null") >= 0)
    {
        // No commands pending
        return;
    }
    
    // Enhanced JSON parsing for command detection (case-insensitive)
    string json_lower = json_commands;
    StringToLower(json_lower);
    
    // Process PAUSE command
    if(StringFind(json_lower, "\"command\":\"pause\"") >= 0 || StringFind(json_lower, "pause") >= 0)
    {
        if(!is_paused) // Only process if not already paused
        {
            is_paused = true;
            SendCommandAck("pause", "executed");
            Print("⏸️ EA PAUSED by COC Dashboard command");
            
            // Send immediate status update to reflect pause state
            SendStatusUpdate();
        }
    }
    
    // Process RESUME command  
    if(StringFind(json_lower, "\"command\":\"resume\"") >= 0 || StringFind(json_lower, "resume") >= 0)
    {
        if(is_paused) // Only process if currently paused
        {
            is_paused = false;
            SendCommandAck("resume", "executed");
            Print("▶️ EA RESUMED by COC Dashboard command");
            
            // Send immediate status update to reflect resume state
            SendStatusUpdate();
        }
    }
    
    // Process CLOSE_POSITIONS command
    if(StringFind(json_lower, "close_positions") >= 0 || StringFind(json_lower, "close_all") >= 0)
    {
        CloseAllPositions();
        SendCommandAck("close_positions", "executed");
        Print("🔒 All positions closed by COC Dashboard command");
    }
    
    // Process ADJUST_RISK command
    if(StringFind(json_lower, "adjust_risk") >= 0 || StringFind(json_lower, "set_risk") >= 0)
    {
        // Check adjustment type
        string adjustment_type = ExtractStringFromJson(json_commands, "adjustment_type");
        double adjustment_value = ExtractDoubleFromJson(json_commands, "adjustment_value");
        
        if(adjustment_type == "lot_size")
        {
            // Direct lot size adjustment
            if(adjustment_value > 0 && adjustment_value <= 10.0) // Reasonable lot limits
            {
                Dynamic_Fixed_Lot_Size = adjustment_value;
                Dynamic_Use_Fixed_Lot = true; // Enable fixed lot mode
                SendCommandAck("adjust_risk", "executed - lot size set to " + DoubleToString(adjustment_value, 2));
                Print("⚠️ Lot size set to ", adjustment_value, " lots by COC Dashboard command");
            }
            else
            {
                SendCommandAck("adjust_risk", "failed - invalid lot size");
                Print("❌ Invalid lot size in adjust_risk command");
            }
        }
        else if(adjustment_type == "stop_loss_pips" || adjustment_type == "stop_loss_points")
        {
            // Stop loss adjustment in pips/points
            if(adjustment_value > 0 && adjustment_value <= 1000) // Reasonable SL limits
            {
                Default_Stop_Loss = adjustment_value;
                SendCommandAck("adjust_risk", "executed - default stop loss set to " + DoubleToString(adjustment_value, 0) + " points");
                Print("🎯 Default stop loss updated to ", adjustment_value, " points by COC Dashboard command");
            }
            else
            {
                SendCommandAck("adjust_risk", "failed - invalid stop loss value (1-1000 points expected, got " + DoubleToString(adjustment_value, 0) + ")");
                Print("❌ Invalid stop loss value: ", adjustment_value, " (expected 1-1000 points)");
            }
        }
        else if(adjustment_type == "take_profit_pips" || adjustment_type == "take_profit_points")
        {
            // Take profit adjustment in pips/points
            if(adjustment_value > 0 && adjustment_value <= 1000) // Reasonable TP limits
            {
                Default_Take_Profit = adjustment_value;
                SendCommandAck("adjust_risk", "executed - default take profit set to " + DoubleToString(adjustment_value, 0) + " points");
                Print("🎯 Default take profit updated to ", adjustment_value, " points by COC Dashboard command");
            }
            else
            {
                SendCommandAck("adjust_risk", "failed - invalid take profit value (1-1000 points expected, got " + DoubleToString(adjustment_value, 0) + ")");
                Print("❌ Invalid take profit value: ", adjustment_value, " (expected 1-1000 points)");
            }
        }
        else if(adjustment_type == "risk_percent" || adjustment_type == "")
        {
            // Risk percentage adjustment (default)
            double new_risk = (adjustment_value > 0) ? adjustment_value : ExtractRiskFromJson(json_commands);
            if(new_risk > 0 && new_risk <= 10.0) // Reasonable risk limits
            {
                Risk_Percent = new_risk;
                Dynamic_Use_Fixed_Lot = false; // Disable fixed lot mode
                SendCommandAck("adjust_risk", "executed - risk percent set to " + DoubleToString(new_risk, 1) + "%");
                Print("⚠️ Risk updated to ", new_risk, "% by COC Dashboard command");
            }
            else
            {
                SendCommandAck("adjust_risk", "failed - invalid risk value (0.1-10.0% expected, got " + DoubleToString(new_risk, 2) + ")");
                Print("❌ Invalid risk value: ", new_risk, " (expected 0.1-10.0%)");
                Print("📋 Received parameters: ", json_commands);
            }
        }
        else
        {
            SendCommandAck("adjust_risk", "failed - unsupported adjustment type");
            Print("❌ Unsupported adjustment type: ", adjustment_type);
        }
    }
    
    // Process PLACE_ORDER command
    if(StringFind(json_lower, "place_order") >= 0)
    {
        ProcessPlaceOrderCommand(json_commands);
    }
    
    // Process MODIFY_ORDER command  
    if(StringFind(json_lower, "modify_order") >= 0)
    {
        ProcessModifyOrderCommand(json_commands);
    }
    
    // Process CANCEL_ORDER command
    if(StringFind(json_lower, "cancel_order") >= 0)
    {
        ProcessCancelOrderCommand(json_commands);
    }
    
    // Process STOP_LOSS adjustment command (only if it's a direct stop_loss command, not adjust_risk)
    if(StringFind(json_lower, "\"command\":\"stop_loss\"") >= 0)
    {
        ProcessStopLossCommand(json_commands);
    }
    
    // Process TAKE_PROFIT adjustment command (only if it's a direct take_profit command, not adjust_risk)
    if(StringFind(json_lower, "\"command\":\"take_profit\"") >= 0)
    {
        ProcessTakeProfitCommand(json_commands);
    }
    
    // Process MAX_POSITIONS command
    if(StringFind(json_lower, "max_positions") >= 0)
    {
        ProcessMaxPositionsCommand(json_commands);
    }
    
    // Process COC OVERRIDE commands
    if(StringFind(json_lower, "enable_coc") >= 0 || StringFind(json_lower, "coc_override") >= 0)
    {
        coc_override = true;
        SendCommandAck("enable_coc_override", "executed");
        Print("🎮 COC Override ENABLED - Manual control active");
    }
    
    if(StringFind(json_lower, "disable_coc") >= 0)
    {
        coc_override = false;
        SendCommandAck("disable_coc_override", "executed");
        Print("🤖 COC Override DISABLED - Auto trading resumed");
    }
    
    // Process EMERGENCY_STOP command
    if(StringFind(json_lower, "emergency_stop") >= 0 || StringFind(json_lower, "stop_all") >= 0)
    {
        is_paused = true;
        CloseAllPositions();
        SendCommandAck("emergency_stop", "executed");
        Print("🚨 EMERGENCY STOP executed by COC Dashboard!");
    }
}

//+------------------------------------------------------------------+
//| Send Command Acknowledgment to Backend                          |
//+------------------------------------------------------------------+
bool SendCommandAck(string command, string status)
{
    string url = Backend_URL + "/api/ea/acknowledge";
    string headers = "Content-Type: application/json\r\n";
    
    string json = "{";
    json += "\"magic_number\":" + IntegerToString(Magic_Number) + ",";
    json += "\"command\":\"" + command + "\",";
    json += "\"status\":\"" + status + "\",";
    json += "\"timestamp\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
    json += "}";
    
    uchar post[], result[];
    StringToCharArray(json, post, 0, StringLen(json));
    
    string result_headers;
    int res = WebRequest("POST", url, headers, 5000, post, result, result_headers);
    
    if(res == 200)
    {
        Print("✅ Command acknowledgment sent: ", command, " - ", status);
        return true;
    }
    else
    {
        Print("❌ Failed to send command acknowledgment. Response code: ", res);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Update Performance Metrics                                      |
//+------------------------------------------------------------------+
void UpdatePerformanceMetrics()
{
    // Update current profit from open positions
    current_profit = 0.0;
    open_positions = 0;
    
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            if(PositionGetInteger(POSITION_MAGIC) == Magic_Number)
            {
                current_profit += PositionGetDouble(POSITION_PROFIT);
                open_positions++;
                
                // Update SL/TP values (from last position for demo)
                sl_value = PositionGetDouble(POSITION_SL);
                tp_value = PositionGetDouble(POSITION_TP);
            }
        }
    }
    
    // Update equity tracking for drawdown calculation
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(current_equity > peak_equity)
        peak_equity = current_equity;
    
    double current_drawdown = (peak_equity - current_equity) / peak_equity * 100.0;
    if(current_drawdown > max_drawdown)
        max_drawdown = current_drawdown;
}

//+------------------------------------------------------------------+
//| Get Module Status JSON                                          |
//+------------------------------------------------------------------+
string GetModuleStatus()
{
    // Simulate module status for demonstration
    string status = "{";
    status += "\"MACD\":\"" + (iMACD(Symbol(), PERIOD_H1, 12, 26, 9, PRICE_CLOSE) > 0 ? "BUY_SIGNAL" : "SELL_SIGNAL") + "\",";
    status += "\"RSI\":\"" + (iRSI(Symbol(), PERIOD_H1, 14, PRICE_CLOSE) > 70 ? "OVERBOUGHT" : (iRSI(Symbol(), PERIOD_H1, 14, PRICE_CLOSE) < 30 ? "OVERSOLD" : "NEUTRAL")) + "\",";
    status += "\"TREND\":\"" + (iMA(Symbol(), PERIOD_H1, 50, 0, MODE_SMA, PRICE_CLOSE) > iMA(Symbol(), PERIOD_H1, 200, 0, MODE_SMA, PRICE_CLOSE) ? "BULLISH" : "BEARISH") + "\"";
    status += "}";
    return status;
}

//+------------------------------------------------------------------+
//| Get Performance Metrics JSON                                    |
//+------------------------------------------------------------------+
string GetPerformanceMetrics()
{
    double profit_factor = total_trades > 0 ? MathAbs(total_profit / MathMax(1.0, total_trades)) : 0.0;
    double expected_payoff = total_trades > 0 ? total_profit / total_trades : 0.0;
    
    string metrics = "{";
    metrics += "\"profit_factor\":" + DoubleToString(profit_factor, 2) + ",";
    metrics += "\"expected_payoff\":" + DoubleToString(expected_payoff, 2) + ",";
    metrics += "\"max_drawdown\":" + DoubleToString(max_drawdown, 2) + ",";
    metrics += "\"total_trades\":" + IntegerToString(total_trades) + ",";
    metrics += "\"win_rate\":" + DoubleToString(70.5, 1); // Demo value
    metrics += "}";
    return metrics;
}

//+------------------------------------------------------------------+
//| Get Recent Trades JSON                                          |
//+------------------------------------------------------------------+
string GetRecentTrades()
{
    string trades = "[";
    
    // Get last 5 deals for this EA
    int deals_count = 0;
    datetime from = TimeCurrent() - 86400; // Last 24 hours
    
    HistorySelect(from, TimeCurrent());
    int total_deals = HistoryDealsTotal();
    
    for(int i = total_deals - 1; i >= 0 && deals_count < 5; i--)
    {
        ulong deal_ticket = HistoryDealGetTicket(i);
        if(deal_ticket > 0 && HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) == Magic_Number)
        {
            if(deals_count > 0) trades += ",";
            
            trades += "{";
            trades += "\"ticket\":" + IntegerToString(deal_ticket) + ",";
            trades += "\"type\":\"" + (HistoryDealGetInteger(deal_ticket, DEAL_TYPE) == DEAL_TYPE_BUY ? "BUY" : "SELL") + "\",";
            trades += "\"volume\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_VOLUME), 2) + ",";
            trades += "\"price\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PRICE), 5) + ",";
            trades += "\"profit\":" + DoubleToString(HistoryDealGetDouble(deal_ticket, DEAL_PROFIT), 2) + ",";
            trades += "\"time\":\"" + TimeToString((datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME), TIME_DATE|TIME_SECONDS) + "\"";
            trades += "}";
            
            deals_count++;
        }
    }
    
    trades += "]";
    return trades;
}

//+------------------------------------------------------------------+
//| Simple Trading Logic (Demo)                                     |
//+------------------------------------------------------------------+
void ExecuteTradingLogic()
{
    // Simple MACD crossover strategy for demonstration
    static double prev_macd = 0;
    
    double macd_main = iMACD(Symbol(), PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
    double macd_signal = iMACD(Symbol(), PERIOD_H1, 12, 26, 9, PRICE_CLOSE); // Simplified
    
    // Only trade if no positions are open
    if(open_positions == 0)
    {
        if(macd_main > macd_signal && prev_macd <= macd_signal)
        {
            // Buy signal
            OpenPosition(ORDER_TYPE_BUY);
        }
        else if(macd_main < macd_signal && prev_macd >= macd_signal)
        {
            // Sell signal
            OpenPosition(ORDER_TYPE_SELL);
        }
    }
    
    prev_macd = macd_main;
}

//+------------------------------------------------------------------+
//| Open Position                                                   |
//+------------------------------------------------------------------+
bool OpenPosition(ENUM_ORDER_TYPE order_type)
{
    double price = (order_type == ORDER_TYPE_BUY) ? SymbolInfoDouble(Symbol(), SYMBOL_ASK) : SymbolInfoDouble(Symbol(), SYMBOL_BID);
    double lot_size = CalculateLotSize();
    
    double sl = 0, tp = 0;
    if(order_type == ORDER_TYPE_BUY)
    {
        sl = price - 100 * SymbolInfoDouble(Symbol(), SYMBOL_POINT);
        tp = price + 200 * SymbolInfoDouble(Symbol(), SYMBOL_POINT);
    }
    else
    {
        sl = price + 100 * SymbolInfoDouble(Symbol(), SYMBOL_POINT);
        tp = price - 200 * SymbolInfoDouble(Symbol(), SYMBOL_POINT);
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_DEAL;
    request.symbol = Symbol();
    request.volume = lot_size;
    request.type = order_type;
    request.price = price;
    request.sl = sl;
    request.tp = tp;
    request.magic = Magic_Number;
    request.comment = "COC_EA_" + IntegerToString(Magic_Number);
    
    if(OrderSend(request, result))
    {
        Print("✅ Position opened: ", EnumToString(order_type), " ", lot_size, " lots at ", price);
        total_trades++;
        return true;
    }
    else
    {
        Print("❌ Failed to open position: ", result.comment);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size Based on Risk                                |
//+------------------------------------------------------------------+
double CalculateLotSize()
{
    double lot_size;
    
    if(Dynamic_Use_Fixed_Lot)
    {
        // Use fixed lot size set by dashboard
        lot_size = Dynamic_Fixed_Lot_Size;
    }
    else
    {
        // Calculate lot size based on risk percentage
        double balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double risk_amount = balance * Risk_Percent / 100.0;
        double tick_value = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
        double stop_loss_points = 100; // Demo: 100 points stop loss
        
        lot_size = risk_amount / (stop_loss_points * tick_value);
    }
    
    // Normalize lot size
    double min_lot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MIN);
    double max_lot = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_MAX);
    double lot_step = SymbolInfoDouble(Symbol(), SYMBOL_VOLUME_STEP);
    
    lot_size = MathMax(min_lot, MathMin(max_lot, MathRound(lot_size / lot_step) * lot_step));
    
    return lot_size;
}

//+------------------------------------------------------------------+
//| Extract Risk Value from JSON Command                            |
//+------------------------------------------------------------------+
double ExtractRiskFromJson(string json_str)
{
    // Simple extraction of risk value from JSON parameters
    // Look for "risk" or "risk_percent" in parameters
    
    int risk_pos = StringFind(json_str, "risk");
    if(risk_pos < 0) return 1.0; // Default risk
    
    // Find the value after "risk"
    int colon_pos = StringFind(json_str, ":", risk_pos);
    if(colon_pos < 0) return 1.0;
    
    // Extract number after colon
    string remaining = StringSubstr(json_str, colon_pos + 1);
    
    // Simple parsing to extract number
    string risk_str = "";
    bool in_number = false;
    
    for(int i = 0; i < StringLen(remaining); i++)
    {
        string char_str = StringSubstr(remaining, i, 1);
        ushort char_code = StringGetCharacter(char_str, 0);
        
        if((char_code >= 48 && char_code <= 57) || char_code == 46) // 0-9 or '.'
        {
            risk_str += char_str;
            in_number = true;
        }
        else if(in_number)
        {
            break; // End of number
        }
    }
    
    if(StringLen(risk_str) > 0)
    {
        return StringToDouble(risk_str);
    }
    
    return 1.0; // Default risk
}

//+------------------------------------------------------------------+
//| Extract String Value from JSON by Key                           |
//+------------------------------------------------------------------+
string ExtractStringFromJson(string json_str, string key)
{
    int key_pos = StringFind(json_str, "\"" + key + "\"");
    if(key_pos < 0) return "";
    
    int colon_pos = StringFind(json_str, ":", key_pos);
    if(colon_pos < 0) return "";
    
    // Skip whitespace and find opening quote
    int quote_start = -1;
    for(int i = colon_pos + 1; i < StringLen(json_str); i++)
    {
        string char_str = StringSubstr(json_str, i, 1);
        if(char_str == "\"")
        {
            quote_start = i + 1;
            break;
        }
    }
    
    if(quote_start < 0) return "";
    
    // Find closing quote
    int quote_end = StringFind(json_str, "\"", quote_start);
    if(quote_end < 0) return "";
    
    return StringSubstr(json_str, quote_start, quote_end - quote_start);
}

//+------------------------------------------------------------------+
//| Extract Double Value from JSON by Key                           |
//+------------------------------------------------------------------+
double ExtractDoubleFromJson(string json_str, string key)
{
    int key_pos = StringFind(json_str, "\"" + key + "\"");
    if(key_pos < 0) return 0.0;
    
    int colon_pos = StringFind(json_str, ":", key_pos);
    if(colon_pos < 0) return 0.0;
    
    // Extract number after colon
    string remaining = StringSubstr(json_str, colon_pos + 1);
    string value_str = "";
    bool in_number = false;
    
    for(int i = 0; i < StringLen(remaining); i++)
    {
        string char_str = StringSubstr(remaining, i, 1);
        ushort char_code = StringGetCharacter(char_str, 0);
        
        if((char_code >= 48 && char_code <= 57) || char_code == 46) // 0-9 or '.'
        {
            value_str += char_str;
            in_number = true;
        }
        else if(in_number)
        {
            break; // End of number
        }
        else if(char_code == 32 || char_code == 9) // Space or tab
        {
            continue; // Skip whitespace
        }
        else if(!in_number)
        {
            continue; // Haven't found number start yet
        }
    }
    
    if(StringLen(value_str) > 0)
    {
        return StringToDouble(value_str);
    }
    
    return 0.0;
}

//+------------------------------------------------------------------+
//| Close All Positions                                             |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByTicket(PositionGetTicket(i)))
        {
            if(PositionGetInteger(POSITION_MAGIC) == Magic_Number)
            {
                MqlTradeRequest request = {};
                MqlTradeResult result = {};
                
                request.action = TRADE_ACTION_DEAL;
                request.symbol = PositionGetString(POSITION_SYMBOL);
                request.volume = PositionGetDouble(POSITION_VOLUME);
                request.type = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
                request.price = (request.type == ORDER_TYPE_SELL) ? SymbolInfoDouble(request.symbol, SYMBOL_BID) : SymbolInfoDouble(request.symbol, SYMBOL_ASK);
                request.magic = Magic_Number;
                request.comment = "COC_CLOSE_ALL";
                
                if(!OrderSend(request, result))
                {
                    Print("❌ Failed to close position: ", result.comment);
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Process PLACE_ORDER command                                     |
//+------------------------------------------------------------------+
void ProcessPlaceOrderCommand(string json_commands)
{
    string order_type = ExtractStringFromJson(json_commands, "order_type");
    double volume = ExtractDoubleFromJson(json_commands, "volume");
    double price = ExtractDoubleFromJson(json_commands, "price");
    double sl = ExtractDoubleFromJson(json_commands, "stop_loss");
    double tp = ExtractDoubleFromJson(json_commands, "take_profit");
    string comment = ExtractStringFromJson(json_commands, "comment");
    
    if(StringLen(order_type) == 0)
    {
        SendCommandAck("place_order", "failed - missing order type");
        return;
    }
    
    // Check if we're at max positions
    if(PositionsTotal() >= Max_Positions)
    {
        SendCommandAck("place_order", "failed - maximum positions reached");
        Print("❌ Cannot place order: Maximum positions (", Max_Positions, ") reached");
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.symbol = Symbol();
    request.magic = Magic_Number;
    request.volume = (volume > 0) ? volume : CalculateLotSize();
    request.deviation = 3;
    request.comment = (StringLen(comment) > 0) ? comment : "COC_DASHBOARD";
    
    if(order_type == "buy" || order_type == "BUY")
    {
        request.action = TRADE_ACTION_DEAL;
        request.type = ORDER_TYPE_BUY;
        request.price = (price > 0) ? price : SymbolInfoDouble(Symbol(), SYMBOL_ASK);
    }
    else if(order_type == "sell" || order_type == "SELL")
    {
        request.action = TRADE_ACTION_DEAL;
        request.type = ORDER_TYPE_SELL;
        request.price = (price > 0) ? price : SymbolInfoDouble(Symbol(), SYMBOL_BID);
    }
    else
    {
        SendCommandAck("place_order", "failed - invalid order type");
        return;
    }
    
    // Set stop loss and take profit
    if(sl > 0) request.sl = sl;
    else if(Default_Stop_Loss > 0) 
    {
        request.sl = (request.type == ORDER_TYPE_BUY) ? 
                     request.price - Default_Stop_Loss * Point() :
                     request.price + Default_Stop_Loss * Point();
    }
    
    if(tp > 0) request.tp = tp;
    else if(Default_Take_Profit > 0)
    {
        request.tp = (request.type == ORDER_TYPE_BUY) ? 
                     request.price + Default_Take_Profit * Point() :
                     request.price - Default_Take_Profit * Point();
    }
    
    if(OrderSend(request, result))
    {
        SendCommandAck("place_order", "executed - Order #" + IntegerToString(result.order));
        Print("✅ Order placed successfully: #", result.order, " Volume: ", request.volume);
    }
    else
    {
        SendCommandAck("place_order", "failed - " + result.comment);
        Print("❌ Failed to place order: ", result.comment);
    }
}

//+------------------------------------------------------------------+
//| Process MODIFY_ORDER command                                    |
//+------------------------------------------------------------------+
void ProcessModifyOrderCommand(string json_commands)
{
    int ticket = (int)ExtractDoubleFromJson(json_commands, "ticket");
    double new_sl = ExtractDoubleFromJson(json_commands, "stop_loss");
    double new_tp = ExtractDoubleFromJson(json_commands, "take_profit");
    double new_price = ExtractDoubleFromJson(json_commands, "price");
    
    if(ticket <= 0)
    {
        SendCommandAck("modify_order", "failed - invalid ticket");
        return;
    }
    
    if(!PositionSelectByTicket(ticket))
    {
        SendCommandAck("modify_order", "failed - position not found");
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_SLTP;
    request.position = ticket;
    request.symbol = PositionGetString(POSITION_SYMBOL);
    request.sl = (new_sl > 0) ? new_sl : PositionGetDouble(POSITION_SL);
    request.tp = (new_tp > 0) ? new_tp : PositionGetDouble(POSITION_TP);
    
    if(OrderSend(request, result))
    {
        SendCommandAck("modify_order", "executed - Position #" + IntegerToString(ticket) + " modified");
        Print("✅ Position modified successfully: #", ticket);
    }
    else
    {
        SendCommandAck("modify_order", "failed - " + result.comment);
        Print("❌ Failed to modify position: ", result.comment);
    }
}

//+------------------------------------------------------------------+
//| Process CANCEL_ORDER command                                    |
//+------------------------------------------------------------------+
void ProcessCancelOrderCommand(string json_commands)
{
    int ticket = (int)ExtractDoubleFromJson(json_commands, "ticket");
    
    if(ticket <= 0)
    {
        SendCommandAck("cancel_order", "failed - invalid ticket");
        return;
    }
    
    if(!OrderSelect(ticket))
    {
        SendCommandAck("cancel_order", "failed - order not found");
        return;
    }
    
    MqlTradeRequest request = {};
    MqlTradeResult result = {};
    
    request.action = TRADE_ACTION_REMOVE;
    request.order = ticket;
    
    if(OrderSend(request, result))
    {
        SendCommandAck("cancel_order", "executed - Order #" + IntegerToString(ticket) + " cancelled");
        Print("✅ Order cancelled successfully: #", ticket);
    }
    else
    {
        SendCommandAck("cancel_order", "failed - " + result.comment);
        Print("❌ Failed to cancel order: ", result.comment);
    }
}

//+------------------------------------------------------------------+
//| Process STOP_LOSS command                                       |
//+------------------------------------------------------------------+
void ProcessStopLossCommand(string json_commands)
{
    double new_sl_points = ExtractDoubleFromJson(json_commands, "stop_loss_points");
    double new_sl_price = ExtractDoubleFromJson(json_commands, "stop_loss_price");
    string target = ExtractStringFromJson(json_commands, "target"); // "all" or specific ticket
    
    if(new_sl_points <= 0 && new_sl_price <= 0)
    {
        SendCommandAck("stop_loss", "failed - invalid stop loss value. Use 'stop_loss_points' or 'stop_loss_price' parameter");
        Print("❌ Stop loss command missing parameters. Expected: stop_loss_points or stop_loss_price");
        Print("📋 Received parameters: ", json_commands);
        return;
    }
    
    // Update default for future trades
    if(new_sl_points > 0)
    {
        Default_Stop_Loss = new_sl_points;
        Print("🎯 Default stop loss updated to ", new_sl_points, " points");
    }
    
    int modified_count = 0;
    
    // Modify existing positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionGetTicket(i) > 0 && PositionGetInteger(POSITION_MAGIC) == Magic_Number)
        {
            ulong ticket = PositionGetTicket(i);
            double position_price = PositionGetDouble(POSITION_PRICE_OPEN);
            double new_sl = 0;
            
            if(new_sl_price > 0)
            {
                new_sl = new_sl_price;
            }
            else if(new_sl_points > 0)
            {
                ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
                new_sl = (pos_type == POSITION_TYPE_BUY) ? 
                         position_price - new_sl_points * Point() :
                         position_price + new_sl_points * Point();
            }
            
            MqlTradeRequest request = {};
            MqlTradeResult result = {};
            
            request.action = TRADE_ACTION_SLTP;
            request.position = ticket;
            request.symbol = PositionGetString(POSITION_SYMBOL);
            request.sl = new_sl;
            request.tp = PositionGetDouble(POSITION_TP);
            
            if(OrderSend(request, result))
            {
                modified_count++;
            }
        }
    }
    
    SendCommandAck("stop_loss", "executed - " + IntegerToString(modified_count) + " positions modified");
    Print("✅ Stop loss updated for ", modified_count, " positions");
}

//+------------------------------------------------------------------+
//| Process TAKE_PROFIT command                                     |
//+------------------------------------------------------------------+
void ProcessTakeProfitCommand(string json_commands)
{
    double new_tp_points = ExtractDoubleFromJson(json_commands, "take_profit_points");
    double new_tp_price = ExtractDoubleFromJson(json_commands, "take_profit_price");
    
    if(new_tp_points <= 0 && new_tp_price <= 0)
    {
        SendCommandAck("take_profit", "failed - invalid take profit value. Use 'take_profit_points' or 'take_profit_price' parameter");
        Print("❌ Take profit command missing parameters. Expected: take_profit_points or take_profit_price");
        Print("📋 Received parameters: ", json_commands);
        return;
    }
    
    // Update default for future trades
    if(new_tp_points > 0)
    {
        Default_Take_Profit = new_tp_points;
        Print("🎯 Default take profit updated to ", new_tp_points, " points");
    }
    
    int modified_count = 0;
    
    // Modify existing positions
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionGetTicket(i) > 0 && PositionGetInteger(POSITION_MAGIC) == Magic_Number)
        {
            ulong ticket = PositionGetTicket(i);
            double position_price = PositionGetDouble(POSITION_PRICE_OPEN);
            double new_tp = 0;
            
            if(new_tp_price > 0)
            {
                new_tp = new_tp_price;
            }
            else if(new_tp_points > 0)
            {
                ENUM_POSITION_TYPE pos_type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
                new_tp = (pos_type == POSITION_TYPE_BUY) ? 
                         position_price + new_tp_points * Point() :
                         position_price - new_tp_points * Point();
            }
            
            MqlTradeRequest request = {};
            MqlTradeResult result = {};
            
            request.action = TRADE_ACTION_SLTP;
            request.position = ticket;
            request.symbol = PositionGetString(POSITION_SYMBOL);
            request.sl = PositionGetDouble(POSITION_SL);
            request.tp = new_tp;
            
            if(OrderSend(request, result))
            {
                modified_count++;
            }
        }
    }
    
    SendCommandAck("take_profit", "executed - " + IntegerToString(modified_count) + " positions modified");
    Print("✅ Take profit updated for ", modified_count, " positions");
}

//+------------------------------------------------------------------+
//| Process MAX_POSITIONS command                                   |
//+------------------------------------------------------------------+
void ProcessMaxPositionsCommand(string json_commands)
{
    int new_max = (int)ExtractDoubleFromJson(json_commands, "max_positions");
    
    if(new_max < 1 || new_max > 20) // Reasonable limits
    {
        SendCommandAck("max_positions", "failed - invalid max positions (1-20)");
        return;
    }
    
    Max_Positions = new_max;
    SendCommandAck("max_positions", "executed - max positions set to " + IntegerToString(new_max));
    Print("🔢 Maximum positions updated to ", new_max);
}

//+------------------------------------------------------------------+
//| End of Expert Advisor                                           |
//+------------------------------------------------------------------+
