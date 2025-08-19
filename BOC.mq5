///+------------------------------------------------------------------+
//|                                  BOC Range Breakout EA Enhanced |
//|                           Enhanced with COC Dashboard Integration |
//|                                      Copyright 2020, CompanyName |
//|                                       http://www.companyname.net |
//+------------------------------------------------------------------+
//|                                                                  |
//| 🎛️ COC DASHBOARD INTEGRATION FEATURES:                          |
//| ✅ Real-time EA monitoring and control                          |
//| ✅ Remote command execution (PAUSE/RESUME/CLOSE_ALL)           |
//| ✅ Live performance tracking and statistics                     |
//| ✅ JSON data export for external analysis                       |
//| ✅ Enhanced dashboard with COC status indicators               |
//| ✅ Remote parameter updates (risk %, lot size)                 |
//| ✅ WebSocket-style communication with backend                   |
//| ✅ Automatic registration with COC backend                     |
//| ✅ Graceful shutdown with final status reporting               |
//|                                                                  |
//| To enable COC Dashboard:                                         |
//| 1. Set "Enable_COC_Dashboard" = true in inputs                 |
//| 2. Configure "COC_Backend_URL" (default: http://127.0.0.1:80)  |
//| 3. Run the COC Dashboard backend system                        |
//| 4. EA will auto-register and start reporting                   |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.00"
#property strict
 
 
 
#ifdef __MQL5__
#ifndef __MT4ORDERS__

// #define MT4ORDERS_BYPASS_MAXTIME 1000000 // Max time (in microseconds) to wait for the trading environment synchronization

#ifdef MT4ORDERS_BYPASS_MAXTIME
#include <fxsaber\TradesID\ByPass.mqh> // https://www.mql5.com/en/code/34173
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

// #define MT4ORDERS_BENCHMARK_MINTIME 1000 // Minimum time for the performance alert trigger.

#ifdef MT4ORDERS_BENCHMARK_MINTIME
#include <fxsaber\Benchmark\Benchmark.mqh> // https://www.mql5.com/en/code/31279

#define _B2(A) _B(A, MT4ORDERS_BENCHMARK_MINTIME)
#define _B3(A) _B(A, 1)
#define _BV2(A) _BV(A, MT4ORDERS_BENCHMARK_MINTIME)
#else // MT4ORDERS_BENCHMARK_MINTIME
#define _B2(A) (A)
#define _B3(A) (A)
#define _BV2(A) { A; }
#endif // MT4ORDERS_BENCHMARK_MINTIME

#define __MT4ORDERS__ "2021.06.01"
#define MT4ORDERS_SLTP_OLD // Enabling the old mechanism of identifying the SL/TP of closed positions via OrderClose
// #define MT4ORDERS_TESTER_SELECT_BY_TICKET // Forces SELECT_BY_TICKET to work in the Tester only via OrderTicketID().

#ifdef MT4_TICKET_TYPE
#define TICKET_TYPE int
#define MAGIC_TYPE  int

#undef MT4_TICKET_TYPE
#else // MT4_TICKET_TYPE
#define TICKET_TYPE long // Negative values are also needed for OrderSelectByTicket.
#define MAGIC_TYPE  long
#endif // MT4_TICKET_TYPE

struct MT4_ORDER
  {
   long              Ticket;
   int               Type;

   long              TicketOpen;
   long              TicketID;

   double            Lots;

   string            Symbol;
   string            Comment;

   double            OpenPriceRequest;
   double            OpenPrice;

   long              OpenTimeMsc;
   datetime          OpenTime;

   ENUM_DEAL_REASON  OpenReason;

   double            StopLoss;
   double            TakeProfit;

   double            ClosePriceRequest;
   double            ClosePrice;

   long              CloseTimeMsc;
   datetime          CloseTime;

   ENUM_DEAL_REASON  CloseReason;

   ENUM_ORDER_STATE  State;

   datetime          Expiration;

   long              MagicNumber;

   double            Profit;

   double            Commission;
   double            Swap;

#define POSITION_SELECT (-1)
#define ORDER_SELECT (-2)

   static int        GetDigits(double Price)
     {
      int Res = 0;

      while((bool)(Price = ::NormalizeDouble(Price - (int)Price, 8)))
        {
         Price *= 10;

         Res++;
        }

      return(Res);
     }

   static string     DoubleToString(const double Num, const int digits)
     {
      return(::DoubleToString(Num, ::MathMax(digits, MT4_ORDER::GetDigits(Num))));
     }

   static string     TimeToString(const long time)
     {
      return((string)(datetime)(time / 1000) + "." + ::IntegerToString(time % 1000, 3, '0'));
     }

   static const MT4_ORDER GetPositionData(void)
     {
      MT4_ORDER Res = {};

      Res.Ticket = ::PositionGetInteger(POSITION_TICKET);
      Res.Type = (int)::PositionGetInteger(POSITION_TYPE);

      Res.Lots = ::PositionGetDouble(POSITION_VOLUME);

      Res.Symbol = ::PositionGetString(POSITION_SYMBOL);
      //    Res.Comment = NULL; // MT4ORDERS::CheckPositionCommissionComment();

      Res.OpenPrice = ::PositionGetDouble(POSITION_PRICE_OPEN);
      Res.OpenTimeMsc = (datetime)::PositionGetInteger(POSITION_TIME_MSC);

      Res.StopLoss = ::PositionGetDouble(POSITION_SL);
      Res.TakeProfit = ::PositionGetDouble(POSITION_TP);

      Res.ClosePrice = ::PositionGetDouble(POSITION_PRICE_CURRENT);
      Res.CloseTimeMsc = 0;

      Res.Expiration = 0;

      Res.MagicNumber = ::PositionGetInteger(POSITION_MAGIC);

      Res.Profit = ::PositionGetDouble(POSITION_PROFIT);

      Res.Swap = ::PositionGetDouble(POSITION_SWAP);

      //    Res.Commission = UNKNOWN_COMMISSION; // MT4ORDERS::CheckPositionCommissionComment();

      return(Res);
     }

   static const MT4_ORDER GetOrderData(void)
     {
      MT4_ORDER Res = {};

      Res.Ticket = ::OrderGetInteger(ORDER_TICKET);
      Res.Type = (int)::OrderGetInteger(ORDER_TYPE);

      Res.Lots = ::OrderGetDouble(ORDER_VOLUME_CURRENT);

      Res.Symbol = ::OrderGetString(ORDER_SYMBOL);
      Res.Comment = ::OrderGetString(ORDER_COMMENT);

      Res.OpenPrice = ::OrderGetDouble(ORDER_PRICE_OPEN);
      Res.OpenTimeMsc = (datetime)::OrderGetInteger(ORDER_TIME_SETUP_MSC);

      Res.StopLoss = ::OrderGetDouble(ORDER_SL);
      Res.TakeProfit = ::OrderGetDouble(ORDER_TP);

      Res.ClosePrice = ::OrderGetDouble(ORDER_PRICE_CURRENT);
      Res.CloseTimeMsc = 0; // (datetime)::OrderGetInteger(ORDER_TIME_DONE)

      Res.Expiration = (datetime)::OrderGetInteger(ORDER_TIME_EXPIRATION);

      Res.MagicNumber = ::OrderGetInteger(ORDER_MAGIC);

      Res.Profit = 0;

      Res.Commission = 0;
      Res.Swap = 0;

      if(!Res.OpenPrice)
         Res.OpenPrice = Res.ClosePrice;

      return(Res);
     }

   string            ToString(void) const
     {
      static const string Types[] = {"buy", "sell", "buy limit", "sell limit", "buy stop", "sell stop", "balance"};
      const int digits = (int)::SymbolInfoInteger(this.Symbol, SYMBOL_DIGITS);

      MT4_ORDER TmpOrder = {};

      if(this.Ticket == POSITION_SELECT)
        {
         TmpOrder = MT4_ORDER::GetPositionData();

         TmpOrder.Comment = this.Comment;
         TmpOrder.Commission = this.Commission;
        }
      else
         if(this.Ticket == ORDER_SELECT)
            TmpOrder = MT4_ORDER::GetOrderData();

      return(((this.Ticket == POSITION_SELECT) || (this.Ticket == ORDER_SELECT)) ? TmpOrder.ToString() :
             ("#" + (string)this.Ticket + " " +
              MT4_ORDER::TimeToString(this.OpenTimeMsc) + " " +
              ((this.Type < ::ArraySize(Types)) ? Types[this.Type] : "unknown") + " " +
              MT4_ORDER::DoubleToString(this.Lots, 2) + " " +
              (::StringLen(this.Symbol) ? this.Symbol + " " : NULL) +
              MT4_ORDER::DoubleToString(this.OpenPrice, digits) + " " +
              MT4_ORDER::DoubleToString(this.StopLoss, digits) + " " +
              MT4_ORDER::DoubleToString(this.TakeProfit, digits) + " " +
              ((this.CloseTimeMsc > 0) ? (MT4_ORDER::TimeToString(this.CloseTimeMsc) + " ") : "") +
              MT4_ORDER::DoubleToString(this.ClosePrice, digits) + " " +
              MT4_ORDER::DoubleToString(::NormalizeDouble(this.Commission, 3), 2) + " " + // Больше трех цифр после запятой не выводим.
              MT4_ORDER::DoubleToString(this.Swap, 2) + " " +
              MT4_ORDER::DoubleToString(this.Profit, 2) + " " +
              ((this.Comment == "") ? "" : (this.Comment + " ")) +
              (string)this.MagicNumber +
              (((this.Expiration > 0) ? (" expiration " + (string)this.Expiration): ""))));
     }
  };

#define RESERVE_SIZE 1000
#define DAY (24 * 3600)
#define HISTORY_PAUSE (MT4HISTORY::IsTester ? 0 : 5)
#define END_TIME D'31.12.3000 23:59:59'
#define THOUSAND 1000
#define LASTTIME(A)                                          \
  if (Time##A >= LastTimeMsc)                                \
  {                                                          \
    const datetime TmpTime = (datetime)(Time##A / THOUSAND); \
                                                             \
    if (TmpTime > this.LastTime)                             \
    {                                                        \
      this.LastTotalOrders = 0;                              \
      this.LastTotalDeals = 0;                               \
                                                             \
      this.LastTime = TmpTime;                               \
      LastTimeMsc = this.LastTime * THOUSAND;                \
    }                                                        \
                                                             \
    this.LastTotal##A##s++;                                  \
  }

#ifndef MT4ORDERS_FASTHISTORY_OFF
#include <Generic\HashMap.mqh>
#endif // MT4ORDERS_FASTHISTORY_OFF

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
class MT4HISTORY  
  {
private:
   static const bool MT4HISTORY::IsTester;
   //  static long MT4HISTORY::AccountNumber;

#ifndef MT4ORDERS_FASTHISTORY_OFF
   CHashMap<ulong, ulong> DealsIn;  // By PositionID, it returns DealIn.
   CHashMap<ulong, ulong> DealsOut; // By PositionID, it returns DealOut.
#endif // MT4ORDERS_FASTHISTORY_OFF

   long              Tickets[];
   uint              Amount;

   int               LastTotalDeals;
   int               LastTotalOrders;

#ifdef MT4ORDERS_HISTORY_OLD

   datetime          LastTime;
   datetime          LastInitTime;

   int               PrevDealsTotal;
   int               PrevOrdersTotal;

   // https://www.mql5.com/ru/forum/93352/page50#comment_18040243
   bool              IsChangeHistory(void)
     {
      bool Res = !_B2(::HistorySelect(0, INT_MAX));

      if(!Res)
        {
         const int iDealsTotal = ::HistoryDealsTotal();
         const int iOrdersTotal = ::HistoryOrdersTotal();

         if(Res = (iDealsTotal != this.PrevDealsTotal) || (iOrdersTotal != this.PrevOrdersTotal))
           {
            this.PrevDealsTotal = iDealsTotal;
            this.PrevOrdersTotal = iOrdersTotal;
           }
        }

      return(Res);
     }

   bool              RefreshHistory(void)
     {
      bool Res = !MT4HISTORY::IsChangeHistory();

      if(!Res)
        {
         const datetime LastTimeCurrent = ::TimeCurrent();

         if(!MT4HISTORY::IsTester && ((LastTimeCurrent >= this.LastInitTime + DAY)/* || (MT4HISTORY::AccountNumber != ::AccountInfoInteger(ACCOUNT_LOGIN))*/))
           {
            //  MT4HISTORY::AccountNumber = ::AccountInfoInteger(ACCOUNT_LOGIN);

            this.LastTime = 0;

            this.LastTotalOrders = 0;
            this.LastTotalDeals = 0;

            this.Amount = 0;

            ::ArrayResize(this.Tickets, this.Amount, RESERVE_SIZE);

            this.LastInitTime = LastTimeCurrent;

#ifndef MT4ORDERS_FASTHISTORY_OFF
            this.DealsIn.Clear();
            this.DealsOut.Clear();
#endif // MT4ORDERS_FASTHISTORY_OFF
           }

         const datetime LastTimeCurrentLeft = LastTimeCurrent - HISTORY_PAUSE;

         // If LastTime is equal to zero, then HistorySelect has already been done in MT4HISTORY::IsChangeHistory().
         if(!this.LastTime || _B2(::HistorySelect(this.LastTime, END_TIME)))  // https://www.mql5.com/ru/forum/285631/page79#comment_9884935
            //    if (_B2(::HistorySelect(this.LastTime, INT_MAX))) // Perhaps INT_MAX is faster than END_TIME
           {
            const int TotalOrders = ::HistoryOrdersTotal();
            const int TotalDeals = ::HistoryDealsTotal();

            Res = ((TotalOrders > this.LastTotalOrders) || (TotalDeals > this.LastTotalDeals));

            if(Res)
              {
               int iOrder = this.LastTotalOrders;
               int iDeal = this.LastTotalDeals;

               ulong TicketOrder = 0;
               ulong TicketDeal = 0;

               long TimeOrder = (iOrder < TotalOrders) ? ::HistoryOrderGetInteger((TicketOrder = ::HistoryOrderGetTicket(iOrder)), ORDER_TIME_DONE_MSC) : LONG_MAX;
               long TimeDeal = (iDeal < TotalDeals) ? ::HistoryDealGetInteger((TicketDeal = ::HistoryDealGetTicket(iDeal)), DEAL_TIME_MSC) : LONG_MAX;

               if(this.LastTime < LastTimeCurrentLeft)
                 {
                  this.LastTotalOrders = 0;
                  this.LastTotalDeals = 0;

                  this.LastTime = LastTimeCurrentLeft;
                 }

               long LastTimeMsc = this.LastTime * THOUSAND;

               while((iDeal < TotalDeals) || (iOrder < TotalOrders))
                  if(TimeOrder < TimeDeal)
                    {
                     LASTTIME(Order)

                     if(MT4HISTORY::IsMT4Order(TicketOrder))
                       {
                        this.Amount = ::ArrayResize(this.Tickets, this.Amount + 1, RESERVE_SIZE);

                        this.Tickets[this.Amount - 1] = -(long)TicketOrder;
                       }

                     iOrder++;

                     TimeOrder = (iOrder < TotalOrders) ? ::HistoryOrderGetInteger((TicketOrder = ::HistoryOrderGetTicket(iOrder)), ORDER_TIME_DONE_MSC) : LONG_MAX;
                    }
                  else
                    {
                     LASTTIME(Deal)

                     if(MT4HISTORY::IsMT4Deal(TicketDeal))
                       {
                        this.Amount = ::ArrayResize(this.Tickets, this.Amount + 1, RESERVE_SIZE);

                        this.Tickets[this.Amount - 1] = (long)TicketDeal;

#ifndef MT4ORDERS_FASTHISTORY_OFF
                        _B2(this.DealsOut.Add(::HistoryDealGetInteger(TicketDeal, DEAL_POSITION_ID), TicketDeal));
#endif // MT4ORDERS_FASTHISTORY_OFF
                       }
#ifndef MT4ORDERS_FASTHISTORY_OFF
                     else
                        if((ENUM_DEAL_ENTRY)::HistoryDealGetInteger(TicketDeal, DEAL_ENTRY) == DEAL_ENTRY_IN)
                           _B2(this.DealsIn.Add(::HistoryDealGetInteger(TicketDeal, DEAL_POSITION_ID), TicketDeal));
#endif // MT4ORDERS_FASTHISTORY_OFF

                     iDeal++;

                     TimeDeal = (iDeal < TotalDeals) ? ::HistoryDealGetInteger((TicketDeal = ::HistoryDealGetTicket(iDeal)), DEAL_TIME_MSC) : LONG_MAX;
                    }
              }
            else
               if(LastTimeCurrentLeft > this.LastTime)
                 {
                  this.LastTime = LastTimeCurrentLeft;

                  this.LastTotalOrders = 0;
                  this.LastTotalDeals = 0;
                 }
           }
        }

      return(Res);
     }

#else // #ifdef MT4ORDERS_HISTORY_OLD
   bool              RefreshHistory(void)
     {
      if(_B2(::HistorySelect(0, INT_MAX)))
        {
         const int TotalOrders = ::HistoryOrdersTotal();
         const int TotalDeals = ::HistoryDealsTotal();

         if((TotalOrders > this.LastTotalOrders) || (TotalDeals > this.LastTotalDeals))
           {
            ulong TicketOrder = 0;
            ulong TicketDeal = 0;

            long TimeOrder = (this.LastTotalOrders < TotalOrders) ?
                             ::HistoryOrderGetInteger((TicketOrder = ::HistoryOrderGetTicket(this.LastTotalOrders)), ORDER_TIME_DONE_MSC) : LONG_MAX;
            long TimeDeal = (this.LastTotalDeals < TotalDeals) ?
                            ::HistoryDealGetInteger((TicketDeal = ::HistoryDealGetTicket(this.LastTotalDeals)), DEAL_TIME_MSC) : LONG_MAX;

            while((this.LastTotalDeals < TotalDeals) || (this.LastTotalOrders < TotalOrders))
               if(TimeOrder < TimeDeal)
                 {
                  if(MT4HISTORY::IsMT4Order(TicketOrder))
                    {
                     this.Amount = ::ArrayResize(this.Tickets, this.Amount + 1, RESERVE_SIZE);

                     this.Tickets[this.Amount - 1] = -(long)TicketOrder;
                    }

                  this.LastTotalOrders++;

                  TimeOrder = (this.LastTotalOrders < TotalOrders) ?
                              ::HistoryOrderGetInteger((TicketOrder = ::HistoryOrderGetTicket(this.LastTotalOrders)), ORDER_TIME_DONE_MSC) : LONG_MAX;
                 }
               else
                 {
                  if(MT4HISTORY::IsMT4Deal(TicketDeal))
                    {
                     this.Amount = ::ArrayResize(this.Tickets, this.Amount + 1, RESERVE_SIZE);

                     this.Tickets[this.Amount - 1] = (long)TicketDeal;

                     _B2(this.DealsOut.Add(::HistoryDealGetInteger(TicketDeal, DEAL_POSITION_ID), TicketDeal));
                    }
                  else
                     if((ENUM_DEAL_ENTRY)::HistoryDealGetInteger(TicketDeal, DEAL_ENTRY) == DEAL_ENTRY_IN)
                        _B2(this.DealsIn.Add(::HistoryDealGetInteger(TicketDeal, DEAL_POSITION_ID), TicketDeal));

                  this.LastTotalDeals++;

                  TimeDeal = (this.LastTotalDeals < TotalDeals) ?
                             ::HistoryDealGetInteger((TicketDeal = ::HistoryDealGetTicket(this.LastTotalDeals)), DEAL_TIME_MSC) : LONG_MAX;
                 }
           }
        }

      return(true);
     }
#endif // #ifdef MT4ORDERS_HISTORY_OLD #else
public:
   static bool       IsMT4Deal(const ulong &Ticket)
     {
      const ENUM_DEAL_TYPE DealType = (ENUM_DEAL_TYPE)::HistoryDealGetInteger(Ticket, DEAL_TYPE);
      const ENUM_DEAL_ENTRY DealEntry = (ENUM_DEAL_ENTRY)::HistoryDealGetInteger(Ticket, DEAL_ENTRY);

      return(((DealType != DEAL_TYPE_BUY) && (DealType != DEAL_TYPE_SELL)) ||      // non trading deal
             ((DealEntry == DEAL_ENTRY_OUT) || (DealEntry == DEAL_ENTRY_OUT_BY))); // trading
     }

   static bool       IsMT4Order(const ulong &Ticket)
     {
      // If the pending order has been executed, its ORDER_POSITION_ID is filled out.
      // https://www.mql5.com/ru/forum/170952/page70#comment_6543162
      // https://www.mql5.com/ru/forum/93352/page19#comment_6646726
      // The second condition: when a limit order has been partially executed and then deleted.
      return(!::HistoryOrderGetInteger(Ticket, ORDER_POSITION_ID) || (::HistoryOrderGetDouble(Ticket, ORDER_VOLUME_CURRENT) &&
             ::HistoryOrderGetInteger(Ticket, ORDER_TYPE) > ORDER_TYPE_SELL));
     }

                     MT4HISTORY(void) : Amount(::ArrayResize(this.Tickets, 0, RESERVE_SIZE)),
                     LastTotalDeals(0), LastTotalOrders(0)
#ifdef MT4ORDERS_HISTORY_OLD
      ,              LastTime(0), LastInitTime(0), PrevDealsTotal(0), PrevOrdersTotal(0)
#endif // #ifdef MT4ORDERS_HISTORY_OLD
     {
      //    this.RefreshHistory(); // If history is not used, there is no point in wasting resources.
     }

   ulong             GetPositionDealIn(const ulong PositionIdentifier = -1)   // 0 is not available, since the tester's balance trade is zero
     {
      ulong Ticket = 0;

      if(PositionIdentifier == -1)
        {
         const ulong MyPositionIdentifier = ::PositionGetInteger(POSITION_IDENTIFIER);

#ifndef MT4ORDERS_FASTHISTORY_OFF
         if(!_B2(this.DealsIn.TryGetValue(MyPositionIdentifier, Ticket))
#ifndef MT4ORDERS_HISTORY_OLD
            && !_B2(this.RefreshHistory() && this.DealsIn.TryGetValue(MyPositionIdentifier, Ticket))
#endif // #ifndef MT4ORDERS_HISTORY_OLD
           )
#endif // MT4ORDERS_FASTHISTORY_OFF
           {
            const datetime PosTime = (datetime)::PositionGetInteger(POSITION_TIME);

            if(_B3(::HistorySelect(PosTime, PosTime)))
              {
               const int Total = ::HistoryDealsTotal();

               for(int i = 0; i < Total; i++)
                 {
                  const ulong TicketDeal = ::HistoryDealGetTicket(i);

                  if((::HistoryDealGetInteger(TicketDeal, DEAL_POSITION_ID) == MyPositionIdentifier) /*&&
                ((ENUM_DEAL_ENTRY)::HistoryDealGetInteger(TicketDeal, DEAL_ENTRY) == DEAL_ENTRY_IN) */) // First mention will be DEAL_ENTRY_IN anyway
                    {
                     Ticket = TicketDeal;

#ifndef MT4ORDERS_FASTHISTORY_OFF
                     _B2(this.DealsIn.Add(MyPositionIdentifier, Ticket));
#endif // MT4ORDERS_FASTHISTORY_OFF

                     break;
                    }
                 }
              }
           }
        }
      else
         if(PositionIdentifier &&  // PositionIdentifier of balance trades is zero
#ifndef MT4ORDERS_FASTHISTORY_OFF
            !_B2(this.DealsIn.TryGetValue(PositionIdentifier, Ticket)) &&
#ifndef MT4ORDERS_HISTORY_OLD
            !_B2(this.RefreshHistory() && this.DealsIn.TryGetValue(PositionIdentifier, Ticket)) &&
#endif // #ifndef MT4ORDERS_HISTORY_OLD
#endif // MT4ORDERS_FASTHISTORY_OFF
            _B3(::HistorySelectByPosition(PositionIdentifier)) && (::HistoryDealsTotal() > 1)) // Why > 1, not > 0 ?!
           {
            Ticket = _B2(::HistoryDealGetTicket(0)); // First mention will be DEAL_ENTRY_IN anyway

            /*
            const int Total = ::HistoryDealsTotal();

            for (int i = 0; i < Total; i++)
            {
              const ulong TicketDeal = ::HistoryDealGetTicket(i);

              if (TicketDeal > 0)
                if ((ENUM_DEAL_ENTRY)::HistoryDealGetInteger(TicketDeal, DEAL_ENTRY) == DEAL_ENTRY_IN)
                {
                  Ticket = TicketDeal;

                  break;
                }
            } */

#ifndef MT4ORDERS_FASTHISTORY_OFF
            _B2(this.DealsIn.Add(PositionIdentifier, Ticket));
#endif // MT4ORDERS_FASTHISTORY_OFF
           }

      return(Ticket);
     }

   ulong             GetPositionDealOut(const ulong PositionIdentifier)
     {
      ulong Ticket = 0;

#ifndef MT4ORDERS_FASTHISTORY_OFF
      if(!_B2(this.DealsOut.TryGetValue(PositionIdentifier, Ticket)) && _B2(this.RefreshHistory()))
         _B2(this.DealsOut.TryGetValue(PositionIdentifier, Ticket));
#endif // MT4ORDERS_FASTHISTORY_OFF

      return(Ticket);
     }

   int               GetAmount(void)
     {
      _B2(this.RefreshHistory());

      return((int)this.Amount);
     }

   long              operator [](const uint &Pos)
     {
      long Res = 0;

      if((Pos >= this.Amount)/* || (!MT4HISTORY::IsTester && (MT4HISTORY::AccountNumber != ::AccountInfoInteger(ACCOUNT_LOGIN)))*/)
        {
         _B2(this.RefreshHistory());

         if(Pos < this.Amount)
            Res = this.Tickets[Pos];
        }
      else
         Res = this.Tickets[Pos];

      return(Res);
     }
  };

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static const bool MT4HISTORY::IsTester = ::MQLInfoInteger(MQL_TESTER);
// static long MT4HISTORY::AccountNumber = ::AccountInfoInteger(ACCOUNT_LOGIN);

#undef LASTTIME
#undef THOUSAND
#undef END_TIME
#undef HISTORY_PAUSE
#undef DAY
#undef RESERVE_SIZE

#define OP_BUY ORDER_TYPE_BUY
#define OP_SELL ORDER_TYPE_SELL
#define OP_BUYLIMIT ORDER_TYPE_BUY_LIMIT
#define OP_SELLLIMIT ORDER_TYPE_SELL_LIMIT
#define OP_BUYSTOP ORDER_TYPE_BUY_STOP
#define OP_SELLSTOP ORDER_TYPE_SELL_STOP
#define OP_BALANCE 6

#define SELECT_BY_POS 0
#define SELECT_BY_TICKET 1

#define MODE_TRADES 0
#define MODE_HISTORY 1

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
class MT4ORDERS
  {
private:
   static MT4_ORDER  Order;
   static MT4HISTORY History;

   static const bool MT4ORDERS::IsTester;
   static const bool MT4ORDERS::IsHedging;

   static int        OrderSendBug;

   //  static bool HistorySelectOrder( const ulong &Ticket )
   static bool       HistorySelectOrder(const ulong Ticket)
     {
      return(Ticket && ((::HistoryOrderGetInteger(Ticket, ORDER_TICKET) == Ticket) ||
                        (_B2(::HistorySelect(0, INT_MAX)) && (::HistoryOrderGetInteger(Ticket, ORDER_TICKET) == Ticket))));
     }

   static bool       HistorySelectDeal(const ulong &Ticket)
     {
      return(Ticket && ((::HistoryDealGetInteger(Ticket, DEAL_TICKET) == Ticket) ||
                        (_B2(::HistorySelect(0, INT_MAX)) && (::HistoryDealGetInteger(Ticket, DEAL_TICKET) == Ticket))));
     }

#define UNKNOWN_COMMISSION DBL_MIN
#define UNKNOWN_REQUEST_PRICE DBL_MIN
#define UNKNOWN_TICKET 0
   // #define UNKNOWN_REASON (-1)

   static bool       CheckNewTicket(void)
     {
      return(false); // This functionality is useless - there is INT_MIN/INT_MAX with SELECT_BY_POS + MODE_TRADES

      static long PrevPosTimeUpdate = 0;
      static long PrevPosTicket = 0;

      const long PosTimeUpdate = ::PositionGetInteger(POSITION_TIME_UPDATE_MSC);
      const long PosTicket = ::PositionGetInteger(POSITION_TICKET);

      // In case that the user has not chosen a position via MT4Orders
      // There is no reason to overload MQL5-PositionSelect* and MQL5-OrderSelect.
      // This check is sufficient, since several changes of position + PositionSelect per millisecond are only possible in tester
      const bool Res = ((PosTimeUpdate != PrevPosTimeUpdate) || (PosTicket != PrevPosTicket));

      if(Res)
        {
         MT4ORDERS::GetPositionData();

         PrevPosTimeUpdate = PosTimeUpdate;
         PrevPosTicket = PosTicket;
        }

      return(Res);
     }

   static bool       CheckPositionTicketOpen(void)
     {
      if((MT4ORDERS::Order.TicketOpen == UNKNOWN_TICKET) || MT4ORDERS::CheckNewTicket())
         MT4ORDERS::Order.TicketOpen = (long)_B2(MT4ORDERS::History.GetPositionDealIn()); // All because of this very expensive function

      return(true);
     }

   static bool       CheckPositionCommissionComment(void)
     {
      if((MT4ORDERS::Order.Commission == UNKNOWN_COMMISSION) || MT4ORDERS::CheckNewTicket())
        {
         MT4ORDERS::Order.Commission = 0; // ::PositionGetDouble(POSITION_COMMISSION); // Always zero
         MT4ORDERS::Order.Comment = ::PositionGetString(POSITION_COMMENT);

         if(!MT4ORDERS::Order.Commission || (MT4ORDERS::Order.Comment == ""))
           {
            MT4ORDERS::CheckPositionTicketOpen();

            const ulong Ticket = MT4ORDERS::Order.TicketOpen;

            if((Ticket > 0) && _B2(MT4ORDERS::HistorySelectDeal(Ticket)))
              {
               if(!MT4ORDERS::Order.Commission)
                 {
                  const double LotsIn = ::HistoryDealGetDouble(Ticket, DEAL_VOLUME);

                  if(LotsIn > 0)
                     MT4ORDERS::Order.Commission = ::HistoryDealGetDouble(Ticket, DEAL_COMMISSION) * ::PositionGetDouble(POSITION_VOLUME) / LotsIn;
                 }

               if(MT4ORDERS::Order.Comment == "")
                  MT4ORDERS::Order.Comment = ::HistoryDealGetString(Ticket, DEAL_COMMENT);
              }
           }
        }

      return(true);
     }
   /*
     static bool CheckPositionOpenReason( void )
     {
       if ((MT4ORDERS::Order.OpenReason == UNKNOWN_REASON) || MT4ORDERS::CheckNewTicket())
       {
         MT4ORDERS::CheckPositionTicketOpen();

         const ulong Ticket = MT4ORDERS::Order.TicketOpen;

         if ((Ticket > 0) && (MT4ORDERS::IsTester || MT4ORDERS::HistorySelectDeal(Ticket)))
           MT4ORDERS::Order.OpenReason = (ENUM_DEAL_REASON)::HistoryDealGetInteger(Ticket, DEAL_REASON);
       }

       return(true);
     }
   */
   static bool       CheckPositionOpenPriceRequest(void)
     {
      const long PosTicket = ::PositionGetInteger(POSITION_TICKET);

      if(((MT4ORDERS::Order.OpenPriceRequest == UNKNOWN_REQUEST_PRICE) || MT4ORDERS::CheckNewTicket()) &&
         !(MT4ORDERS::Order.OpenPriceRequest = (_B2(MT4ORDERS::HistorySelectOrder(PosTicket)) &&
               (MT4ORDERS::IsTester || (::PositionGetInteger(POSITION_TIME_MSC) ==
                                        ::HistoryOrderGetInteger(PosTicket, ORDER_TIME_DONE_MSC)))) // Is this check necessary?
               ? ::HistoryOrderGetDouble(PosTicket, ORDER_PRICE_OPEN)
               : ::PositionGetDouble(POSITION_PRICE_OPEN)))
         MT4ORDERS::Order.OpenPriceRequest = ::PositionGetDouble(POSITION_PRICE_OPEN); // In case the order price is zero

      return(true);
     }

   static void       GetPositionData(void)
     {
      MT4ORDERS::Order.Ticket = POSITION_SELECT;

      MT4ORDERS::Order.Commission = UNKNOWN_COMMISSION; // MT4ORDERS::CheckPositionCommissionComment();
      MT4ORDERS::Order.OpenPriceRequest = UNKNOWN_REQUEST_PRICE; // MT4ORDERS::CheckPositionOpenPriceRequest()
      MT4ORDERS::Order.TicketOpen = UNKNOWN_TICKET;
      //    MT4ORDERS::Order.OpenReason = UNKNOWN_REASON;

      //    const bool AntoWarning = ::OrderSelect(0); // Resets data of the selected position to zero - may be needed for OrderModify

      return;
     }

   // #undef UNKNOWN_REASON
#undef UNKNOWN_TICKET
#undef UNKNOWN_REQUEST_PRICE
#undef UNKNOWN_COMMISSION

   static void       GetOrderData(void)
     {
      MT4ORDERS::Order.Ticket = ORDER_SELECT;

      //    ::PositionSelectByTicket(0);  // Resets data of the selected position to zero - may be needed for OrderModify

      return;
     }

   static void       GetHistoryOrderData(const ulong Ticket)
     {
      MT4ORDERS::Order.Ticket = ::HistoryOrderGetInteger(Ticket, ORDER_TICKET);
      MT4ORDERS::Order.Type = (int)::HistoryOrderGetInteger(Ticket, ORDER_TYPE);

      MT4ORDERS::Order.TicketOpen = MT4ORDERS::Order.Ticket;
      MT4ORDERS::Order.TicketID = MT4ORDERS::Order.Ticket; // A deleted pending order can have a non-zero POSITION_ID.

      MT4ORDERS::Order.Lots = ::HistoryOrderGetDouble(Ticket, ORDER_VOLUME_CURRENT);

      if(!MT4ORDERS::Order.Lots)
         MT4ORDERS::Order.Lots = ::HistoryOrderGetDouble(Ticket, ORDER_VOLUME_INITIAL);

      MT4ORDERS::Order.Symbol = ::HistoryOrderGetString(Ticket, ORDER_SYMBOL);
      MT4ORDERS::Order.Comment = ::HistoryOrderGetString(Ticket, ORDER_COMMENT);

      MT4ORDERS::Order.OpenTimeMsc = ::HistoryOrderGetInteger(Ticket, ORDER_TIME_SETUP_MSC);
      MT4ORDERS::Order.OpenTime = (datetime)(MT4ORDERS::Order.OpenTimeMsc / 1000);

      MT4ORDERS::Order.OpenPrice = ::HistoryOrderGetDouble(Ticket, ORDER_PRICE_OPEN);
      MT4ORDERS::Order.OpenPriceRequest = MT4ORDERS::Order.OpenPrice;

      MT4ORDERS::Order.OpenReason = (ENUM_DEAL_REASON)::HistoryOrderGetInteger(Ticket, ORDER_REASON);

      MT4ORDERS::Order.StopLoss = ::HistoryOrderGetDouble(Ticket, ORDER_SL);
      MT4ORDERS::Order.TakeProfit = ::HistoryOrderGetDouble(Ticket, ORDER_TP);

      MT4ORDERS::Order.CloseTimeMsc = ::HistoryOrderGetInteger(Ticket, ORDER_TIME_DONE_MSC);
      MT4ORDERS::Order.CloseTime = (datetime)(MT4ORDERS::Order.CloseTimeMsc / 1000);

      MT4ORDERS::Order.ClosePrice = ::HistoryOrderGetDouble(Ticket, ORDER_PRICE_CURRENT);
      MT4ORDERS::Order.ClosePriceRequest = MT4ORDERS::Order.ClosePrice;

      MT4ORDERS::Order.CloseReason = MT4ORDERS::Order.OpenReason;

      MT4ORDERS::Order.State = (ENUM_ORDER_STATE)::HistoryOrderGetInteger(Ticket, ORDER_STATE);

      MT4ORDERS::Order.Expiration = (datetime)::HistoryOrderGetInteger(Ticket, ORDER_TIME_EXPIRATION);

      MT4ORDERS::Order.MagicNumber = ::HistoryOrderGetInteger(Ticket, ORDER_MAGIC);

      MT4ORDERS::Order.Profit = 0;

      MT4ORDERS::Order.Commission = 0;
      MT4ORDERS::Order.Swap = 0;

      return;
     }

   static string     GetTickFlag(uint tickflag)
     {
      string flag = " " + (string)tickflag;

#define TICKFLAG_MACRO(A) flag += ((bool)(tickflag & TICK_FLAG_##A)) ? " TICK_FLAG_" + #A : ""; \
                            tickflag -= tickflag & TICK_FLAG_##A;
      TICKFLAG_MACRO(BID)
      TICKFLAG_MACRO(ASK)
      TICKFLAG_MACRO(LAST)
      TICKFLAG_MACRO(VOLUME)
      TICKFLAG_MACRO(BUY)
      TICKFLAG_MACRO(SELL)
#undef TICKFLAG_MACRO

      if(tickflag)
         flag += " FLAG_UNKNOWN (" + (string)tickflag + ")";

      return(flag);
     }

#define TOSTR(A) " " + #A + " = " + (string)Tick.A
#define TOSTR2(A) " " + #A + " = " + ::DoubleToString(Tick.A, digits)
#define TOSTR3(A) " " + #A + " = " + (string)(A)

   static string     TickToString(const string &Symb, const MqlTick &Tick)
     {
      const int digits = (int)::SymbolInfoInteger(Symb, SYMBOL_DIGITS);

      return(TOSTR3(Symb) + TOSTR(time) + "." + ::IntegerToString(Tick.time_msc % 1000, 3, '0') +
             TOSTR2(bid) + TOSTR2(ask) + TOSTR2(last)+ TOSTR(volume) + MT4ORDERS::GetTickFlag(Tick.flags));
     }

   static string     TickToString(const string &Symb)
     {
      MqlTick Tick = {};

      return(TOSTR3(::SymbolInfoTick(Symb, Tick)) + MT4ORDERS::TickToString(Symb, Tick));
     }

#undef TOSTR3
#undef TOSTR2
#undef TOSTR

   static void       AlertLog(void)
     {
      ::Alert("Please send the logs to the coauthor - https://www.mql5.com/en/users/fxsaber");

      string Str = ::TimeToString(::TimeLocal(), TIME_DATE);
      ::StringReplace(Str, ".", NULL);

      ::Alert(::TerminalInfoString(TERMINAL_PATH) + "\\MQL5\\Logs\\" + Str + ".log");

      return;
     }

   static long       GetTimeCurrent(void)
     {
      long Res = 0;
      MqlTick Tick = {};

      for(int i = ::SymbolsTotal(true) - 1; i >= 0; i--)
        {
         const string SymbName = ::SymbolName(i, true);

         if(!::SymbolInfoInteger(SymbName, SYMBOL_CUSTOM) && ::SymbolInfoTick(SymbName, Tick) && (Tick.time_msc > Res))
            Res = Tick.time_msc;
        }

      return(Res);
     }

   static string     TimeToString(const long time)
     {
      return((string)(datetime)(time / 1000) + "." + ::IntegerToString(time % 1000, 3, '0'));
     }

#define WHILE(A) while ((!(Res = (A))) && MT4ORDERS::Waiting())

#define TOSTR(A)  #A + " = " + (string)(A) + "\n"
#define TOSTR2(A) #A + " = " + ::EnumToString(A) + " (" + (string)(A) + ")\n"

   static void       GetHistoryPositionData(const ulong Ticket)
     {
      MT4ORDERS::Order.Ticket = (long)Ticket;
      MT4ORDERS::Order.TicketID = ::HistoryDealGetInteger(MT4ORDERS::Order.Ticket, DEAL_POSITION_ID);
      MT4ORDERS::Order.Type = (int)::HistoryDealGetInteger(Ticket, DEAL_TYPE);

      if((MT4ORDERS::Order.Type > OP_SELL))
         MT4ORDERS::Order.Type += (OP_BALANCE - OP_SELL - 1);
      else
         MT4ORDERS::Order.Type = 1 - MT4ORDERS::Order.Type;

      MT4ORDERS::Order.Lots = ::HistoryDealGetDouble(Ticket, DEAL_VOLUME);

      MT4ORDERS::Order.Symbol = ::HistoryDealGetString(Ticket, DEAL_SYMBOL);
      MT4ORDERS::Order.Comment = ::HistoryDealGetString(Ticket, DEAL_COMMENT);

      MT4ORDERS::Order.CloseTimeMsc = ::HistoryDealGetInteger(Ticket, DEAL_TIME_MSC);
      MT4ORDERS::Order.CloseTime = (datetime)(MT4ORDERS::Order.CloseTimeMsc / 1000); // (datetime)::HistoryDealGetInteger(Ticket, DEAL_TIME);

      MT4ORDERS::Order.ClosePrice = ::HistoryDealGetDouble(Ticket, DEAL_PRICE);

      MT4ORDERS::Order.CloseReason = (ENUM_DEAL_REASON)::HistoryDealGetInteger(Ticket, DEAL_REASON);

      MT4ORDERS::Order.Expiration = 0;

      MT4ORDERS::Order.MagicNumber = ::HistoryDealGetInteger(Ticket, DEAL_MAGIC);

      MT4ORDERS::Order.Profit = ::HistoryDealGetDouble(Ticket, DEAL_PROFIT);

      MT4ORDERS::Order.Commission = ::HistoryDealGetDouble(Ticket, DEAL_COMMISSION);
      MT4ORDERS::Order.Swap = ::HistoryDealGetDouble(Ticket, DEAL_SWAP);

#ifndef MT4ORDERS_SLTP_OLD
      MT4ORDERS::Order.StopLoss = ::HistoryDealGetDouble(Ticket, DEAL_SL);
      MT4ORDERS::Order.TakeProfit = ::HistoryDealGetDouble(Ticket, DEAL_TP);
#else // MT4ORDERS_SLTP_OLD
      MT4ORDERS::Order.StopLoss = 0;
      MT4ORDERS::Order.TakeProfit = 0;
#endif // MT4ORDERS_SLTP_OLD

      const ulong OrderTicket = (MT4ORDERS::Order.Type < OP_BALANCE) ? ::HistoryDealGetInteger(Ticket, DEAL_ORDER) : 0;
      const ulong PosTicket = MT4ORDERS::Order.TicketID;
      const ulong OpenTicket = (OrderTicket > 0) ? _B2(MT4ORDERS::History.GetPositionDealIn(PosTicket)) : 0;

      if(OpenTicket > 0)
        {
         const ENUM_DEAL_REASON Reason = (ENUM_DEAL_REASON)HistoryDealGetInteger(Ticket, DEAL_REASON);
         const ENUM_DEAL_ENTRY DealEntry = (ENUM_DEAL_ENTRY)::HistoryDealGetInteger(Ticket, DEAL_ENTRY);

         // History (OpenTicket and OrderTicket) is loaded due to GetPositionDealIn, - HistorySelectByPosition
#ifdef MT4ORDERS_FASTHISTORY_OFF
         const bool Res = true;
#else // MT4ORDERS_FASTHISTORY_OFF
         // Partial execution will generate the necessary order - https://www.mql5.com/ru/forum/227423/page2#comment_6543129
         bool Res = MT4ORDERS::IsTester ? MT4ORDERS::HistorySelectOrder(OrderTicket) : MT4ORDERS::Waiting(true);

         // Можно долго ждать в этой ситуации: https://www.mql5.com/ru/forum/170952/page184#comment_17913645
         if(!Res)
            WHILE(_B2(MT4ORDERS::HistorySelectOrder(OrderTicket))) // https://www.mql5.com/ru/forum/304239#comment_10710403
            ;

         if(_B2(MT4ORDERS::HistorySelectDeal(OpenTicket)))  // It will surely work, since OpenTicket is reliably in history.
#endif // MT4ORDERS_FASTHISTORY_OFF
           {
            MT4ORDERS::Order.TicketOpen = (long)OpenTicket;

            MT4ORDERS::Order.OpenReason = (ENUM_DEAL_REASON)HistoryDealGetInteger(OpenTicket, DEAL_REASON);

            MT4ORDERS::Order.OpenPrice = ::HistoryDealGetDouble(OpenTicket, DEAL_PRICE);

            MT4ORDERS::Order.OpenTimeMsc = ::HistoryDealGetInteger(OpenTicket, DEAL_TIME_MSC);
            MT4ORDERS::Order.OpenTime = (datetime)(MT4ORDERS::Order.OpenTimeMsc / 1000);

            const double OpenLots = ::HistoryDealGetDouble(OpenTicket, DEAL_VOLUME);

            if(OpenLots > 0)
               MT4ORDERS::Order.Commission += ::HistoryDealGetDouble(OpenTicket, DEAL_COMMISSION) * MT4ORDERS::Order.Lots / OpenLots;

            //        if (!MT4ORDERS::Order.MagicNumber) // Magic number of a closed position must always be equal to that of the opening deal.
            const long Magic = ::HistoryDealGetInteger(OpenTicket, DEAL_MAGIC);

            if(Magic)
               MT4ORDERS::Order.MagicNumber = Magic;

            //        if (MT4ORDERS::Order.Comment == "") // Comment on a closed position must always be equal to that on the opening deal.
            const string StrComment = ::HistoryDealGetString(OpenTicket, DEAL_COMMENT);

            if(Res)  // OrderTicket may be absent in history, but it may be found among those still alive. It is probably reasonable to wheedle info out of there.
              {
               double OrderPriceOpen = ::HistoryOrderGetDouble(OrderTicket, ORDER_PRICE_OPEN);

#ifdef MT4ORDERS_SLTP_OLD
               if(Reason == DEAL_REASON_TP)
                 {
                  if(!OrderPriceOpen)
                     // https://www.mql5.com/ru/forum/1111/page2820#comment_17749873
                     OrderPriceOpen = (double)::StringSubstr(MT4ORDERS::Order.Comment, MT4ORDERS::IsTester ? 3 : (::StringFind(MT4ORDERS::Order.Comment, "tp ") + 3));

                  MT4ORDERS::Order.TakeProfit = OrderPriceOpen;
                  MT4ORDERS::Order.StopLoss = ::HistoryOrderGetDouble(OrderTicket, ORDER_TP);
                 }
               else
                  if(Reason == DEAL_REASON_SL)
                    {
                     if(!OrderPriceOpen)
                        // https://www.mql5.com/ru/forum/1111/page2820#comment_17749873
                        OrderPriceOpen = (double)::StringSubstr(MT4ORDERS::Order.Comment, MT4ORDERS::IsTester ? 3 : (::StringFind(MT4ORDERS::Order.Comment, "sl ") + 3));

                     MT4ORDERS::Order.StopLoss = OrderPriceOpen;
                     MT4ORDERS::Order.TakeProfit = ::HistoryOrderGetDouble(OrderTicket, ORDER_SL);
                    }
                  else
                     if(!MT4ORDERS::IsTester &&::StringLen(MT4ORDERS::Order.Comment) > 3)
                       {
                        const string PartComment = ::StringSubstr(MT4ORDERS::Order.Comment, 0, 3);

                        if(PartComment == "[tp")
                          {
                           MT4ORDERS::Order.CloseReason = DEAL_REASON_TP;

                           if(!OrderPriceOpen)
                              // https://www.mql5.com/ru/forum/1111/page2820#comment_17749873
                              OrderPriceOpen = (double)::StringSubstr(MT4ORDERS::Order.Comment, MT4ORDERS::IsTester ? 3 : (::StringFind(MT4ORDERS::Order.Comment, "tp ") + 3));

                           MT4ORDERS::Order.TakeProfit = OrderPriceOpen;
                           MT4ORDERS::Order.StopLoss = ::HistoryOrderGetDouble(OrderTicket, ORDER_TP);
                          }
                        else
                           if(PartComment == "[sl")
                             {
                              MT4ORDERS::Order.CloseReason = DEAL_REASON_SL;

                              if(!OrderPriceOpen)
                                 // https://www.mql5.com/ru/forum/1111/page2820#comment_17749873
                                 OrderPriceOpen = (double)::StringSubstr(MT4ORDERS::Order.Comment, MT4ORDERS::IsTester ? 3 : (::StringFind(MT4ORDERS::Order.Comment, "sl ") + 3));

                              MT4ORDERS::Order.StopLoss = OrderPriceOpen;
                              MT4ORDERS::Order.TakeProfit = ::HistoryOrderGetDouble(OrderTicket, ORDER_SL);
                             }
                           else
                             {
                              // Reversed - not an error: see OrderClose.
                              MT4ORDERS::Order.StopLoss = ::HistoryOrderGetDouble(OrderTicket, ORDER_TP);
                              MT4ORDERS::Order.TakeProfit = ::HistoryOrderGetDouble(OrderTicket, ORDER_SL);
                             }
                       }
                     else
                       {
                        // Reversed - not an error: see OrderClose.
                        MT4ORDERS::Order.StopLoss = ::HistoryOrderGetDouble(OrderTicket, ORDER_TP);
                        MT4ORDERS::Order.TakeProfit = ::HistoryOrderGetDouble(OrderTicket, ORDER_SL);
                       }
#endif // MT4ORDERS_SLTP_OLD

               MT4ORDERS::Order.State = (ENUM_ORDER_STATE)::HistoryOrderGetInteger(OrderTicket, ORDER_STATE);

               if(!(MT4ORDERS::Order.ClosePriceRequest = (DealEntry == DEAL_ENTRY_OUT_BY) ? MT4ORDERS::Order.ClosePrice : OrderPriceOpen))
                  MT4ORDERS::Order.ClosePriceRequest = MT4ORDERS::Order.ClosePrice;

               if(!(MT4ORDERS::Order.OpenPriceRequest = _B2(MT4ORDERS::HistorySelectOrder(PosTicket) &&
                     // During partial execution, only the last deal of a fully executed order has this condition for taking the request price.
                     (MT4ORDERS::IsTester || (::HistoryDealGetInteger(OpenTicket, DEAL_TIME_MSC) == ::HistoryOrderGetInteger(PosTicket, ORDER_TIME_DONE_MSC)))) ?
                     ::HistoryOrderGetDouble(PosTicket, ORDER_PRICE_OPEN) : MT4ORDERS::Order.OpenPrice))
                  MT4ORDERS::Order.OpenPriceRequest = MT4ORDERS::Order.OpenPrice;
              }
            else
              {
               MT4ORDERS::Order.State = ORDER_STATE_FILLED;

               MT4ORDERS::Order.ClosePriceRequest = MT4ORDERS::Order.ClosePrice;
               MT4ORDERS::Order.OpenPriceRequest = MT4ORDERS::Order.OpenPrice;
              }

            // The comment above is used to find SL/TP.
            if(StrComment != "")
               MT4ORDERS::Order.Comment = StrComment;
           }

         if(!Res)
           {
            //::Alert("HistoryOrderSelect(" + (string)OrderTicket + ") - BUG! MT4ORDERS - not Sync with History!");
            MT4ORDERS::AlertLog();

            ::Print(__FILE__ + "\nVersion = " + __MT4ORDERS__ + "\nCompiler = " + (string)__MQLBUILD__ + "\n" + TOSTR(__DATE__) +
                    TOSTR(::AccountInfoString(ACCOUNT_SERVER)) + TOSTR2((ENUM_ACCOUNT_TRADE_MODE)::AccountInfoInteger(ACCOUNT_TRADE_MODE)) +
                    TOSTR((bool)::TerminalInfoInteger(TERMINAL_CONNECTED)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_PING_LAST)) + TOSTR(::TerminalInfoDouble(TERMINAL_RETRANSMISSION)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_BUILD)) + TOSTR((bool)::TerminalInfoInteger(TERMINAL_X64)) +
                    TOSTR((bool)::TerminalInfoInteger(TERMINAL_VPS)) + TOSTR2((ENUM_PROGRAM_TYPE)::MQLInfoInteger(MQL_PROGRAM_TYPE)) +
                    TOSTR(::TimeCurrent()) + TOSTR(::TimeTradeServer()) + TOSTR(MT4ORDERS::TimeToString(MT4ORDERS::GetTimeCurrent())) +
                    TOSTR(::SymbolInfoString(MT4ORDERS::Order.Symbol, SYMBOL_PATH)) + TOSTR(::SymbolInfoString(MT4ORDERS::Order.Symbol, SYMBOL_DESCRIPTION)) +
                    "CurrentTick =" + MT4ORDERS::TickToString(MT4ORDERS::Order.Symbol) + "\n" +
                    TOSTR(::PositionsTotal()) + TOSTR(::OrdersTotal()) +
                    TOSTR(::HistorySelect(0, INT_MAX)) + TOSTR(::HistoryDealsTotal()) + TOSTR(::HistoryOrdersTotal()) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_AVAILABLE)) + TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_PHYSICAL)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_TOTAL)) + TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_USED)) +
                    TOSTR(::MQLInfoInteger(MQL_MEMORY_LIMIT)) + TOSTR(::MQLInfoInteger(MQL_MEMORY_USED)) +
                    TOSTR(Ticket) + TOSTR(OrderTicket) + TOSTR(OpenTicket) + TOSTR(PosTicket) +
                    TOSTR(MT4ORDERS::TimeToString(MT4ORDERS::Order.CloseTimeMsc)) +
                    TOSTR(MT4ORDERS::HistorySelectOrder(OrderTicket)) + TOSTR(::OrderSelect(OrderTicket)) +
                    (::OrderSelect(OrderTicket) ? TOSTR2((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE)) : NULL) +
                    (::HistoryDealsTotal() ? TOSTR(::HistoryDealGetTicket(::HistoryDealsTotal() - 1)) +
                     "DEAL_ORDER = " + (string)::HistoryDealGetInteger(::HistoryDealGetTicket(::HistoryDealsTotal() - 1), DEAL_ORDER) + "\n"
                     "DEAL_TIME_MSC = " + MT4ORDERS::TimeToString(::HistoryDealGetInteger(::HistoryDealGetTicket(::HistoryDealsTotal() - 1), DEAL_TIME_MSC)) + "\n"
                     : NULL) +
                    (::HistoryOrdersTotal() ? TOSTR(::HistoryOrderGetTicket(::HistoryOrdersTotal() - 1)) +
                     "ORDER_TIME_DONE_MSC = " + MT4ORDERS::TimeToString(::HistoryOrderGetInteger(::HistoryOrderGetTicket(::HistoryOrdersTotal() - 1), ORDER_TIME_DONE_MSC)) + "\n"
                     : NULL) +
#ifdef MT4ORDERS_BYPASS_MAXTIME
                    "MT4ORDERS::ByPass: " + MT4ORDERS::ByPass.ToString() + "\n" +
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME
                    TOSTR(MT4ORDERS::OrderSend_MaxPause));
           }
        }
      else
        {
         MT4ORDERS::Order.TicketOpen = MT4ORDERS::Order.Ticket;

         if(!MT4ORDERS::Order.TicketID && (MT4ORDERS::Order.Type <= OP_SELL))  // ID of balance deals must remain zero.
            MT4ORDERS::Order.TicketID = MT4ORDERS::Order.Ticket;

         MT4ORDERS::Order.OpenPrice = MT4ORDERS::Order.ClosePrice; // ::HistoryDealGetDouble(Ticket, DEAL_PRICE);

         MT4ORDERS::Order.OpenTimeMsc = MT4ORDERS::Order.CloseTimeMsc;
         MT4ORDERS::Order.OpenTime = MT4ORDERS::Order.CloseTime;   // (datetime)::HistoryDealGetInteger(Ticket, DEAL_TIME);

         MT4ORDERS::Order.OpenReason = MT4ORDERS::Order.CloseReason;

         MT4ORDERS::Order.State = ORDER_STATE_FILLED;

         MT4ORDERS::Order.ClosePriceRequest = MT4ORDERS::Order.ClosePrice;
         MT4ORDERS::Order.OpenPriceRequest = MT4ORDERS::Order.OpenPrice;
        }

      if(OrderTicket)
        {
         bool Res = MT4ORDERS::IsTester ? MT4ORDERS::HistorySelectOrder(OrderTicket) : MT4ORDERS::Waiting(true);

         if(!Res)
            WHILE(_B2(MT4ORDERS::HistorySelectOrder(OrderTicket))) // https://www.mql5.com/ru/forum/304239#comment_10710403
            ;

         if((ENUM_ORDER_TYPE)::HistoryOrderGetInteger(OrderTicket, ORDER_TYPE) == ORDER_TYPE_CLOSE_BY)
           {
            const ulong PosTicketBy = ::HistoryOrderGetInteger(OrderTicket, ORDER_POSITION_BY_ID);

            if(PosTicketBy == PosTicket)  // CloseBy-Slave should not affect the total trade.
              {
               MT4ORDERS::Order.Lots = 0;
               MT4ORDERS::Order.Commission = 0;

               MT4ORDERS::Order.ClosePrice = MT4ORDERS::Order.OpenPrice;
               MT4ORDERS::Order.ClosePriceRequest = MT4ORDERS::Order.ClosePrice;
              }
            else // CloseBy-Master must receive a commission from CloseBy-Slave.
              {
               const ulong OpenTicketBy = (OrderTicket > 0) ? _B2(MT4ORDERS::History.GetPositionDealIn(PosTicketBy)) : 0;

               if((OpenTicketBy > 0) && _B2(MT4ORDERS::HistorySelectDeal(OpenTicketBy)))
                 {
                  const double OpenLots = ::HistoryDealGetDouble(OpenTicketBy, DEAL_VOLUME);

                  if(OpenLots > 0)
                     MT4ORDERS::Order.Commission += ::HistoryDealGetDouble(OpenTicketBy, DEAL_COMMISSION) * MT4ORDERS::Order.Lots / OpenLots;
                 }
              }
           }
        }

      return;
     }

   static bool       Waiting(const bool FlagInit = false)
     {
      static ulong StartTime = 0;

      const bool Res = FlagInit ? false : (::GetMicrosecondCount() - StartTime < MT4ORDERS::OrderSend_MaxPause);

      if(FlagInit)
        {
         StartTime = ::GetMicrosecondCount();

         MT4ORDERS::OrderSendBug = 0;
        }
      else
         if(Res)
           {
            //      ::Sleep(0); // https://www.mql5.com/ru/forum/170952/page100#comment_8750511

            MT4ORDERS::OrderSendBug++;
           }

      return(Res);
     }

   static bool       EqualPrices(const double Price1, const double &Price2, const int &digits)
     {
      return(!::NormalizeDouble(Price1 - Price2, digits));
     }

   static bool       HistoryDealSelect2(MqlTradeResult &Result)   // At the end of the name there is a digit for greater compatibility with macros.
     {
#ifdef MT4ORDERS_HISTORY_OLD
      // Replace HistorySelectByPosition with HistorySelect(PosTime, PosTime)
      if(!Result.deal && Result.order && _B3(::HistorySelectByPosition(::HistoryOrderGetInteger(Result.order, ORDER_POSITION_ID))))
        {
#else // #ifdef MT4ORDERS_HISTORY_OLD
      if(!Result.deal && Result.order && _B2(MT4ORDERS::HistorySelectOrder(Result.order)))
        {
         const long OrderTimeFill = ::HistoryOrderGetInteger(Result.order, ORDER_TIME_DONE_MSC);
#endif // #ifdef MT4ORDERS_HISTORY_OLD #else
         if(::HistorySelect(0, INT_MAX))  // Without it, the deal detection may fail.
            for(int i = ::HistoryDealsTotal() - 1; i >= 0; i--)
              {
               const ulong DealTicket = ::HistoryDealGetTicket(i);

               if(Result.order == ::HistoryDealGetInteger(DealTicket, DEAL_ORDER))
                 {
                  Result.deal = DealTicket;
                  Result.price = ::HistoryDealGetDouble(DealTicket, DEAL_PRICE);

                  break;
                 }
#ifndef MT4ORDERS_HISTORY_OLD
               else
                  if(::HistoryDealGetInteger(DealTicket, DEAL_TIME_MSC) < OrderTimeFill)
                     break;
#endif // #ifndef MT4ORDERS_HISTORY_OLD
              }
        }

      return(_B2(MT4ORDERS::HistorySelectDeal(Result.deal)));
     }

   /*
   #define MT4ORDERS_BENCHMARK Alert(MT4ORDERS::LastTradeRequest.symbol + " " +       \
                                     (string)MT4ORDERS::LastTradeResult.order + " " + \
                                     MT4ORDERS::LastTradeResult.comment);             \
                               Print(ToString(MT4ORDERS::LastTradeRequest) +          \
                                     ToString(MT4ORDERS::LastTradeResult));
   */

#define TMP_MT4ORDERS_BENCHMARK(A) \
  static ulong Max##A = 0;         \
                                   \
  if (Interval##A > Max##A)        \
  {                                \
    MT4ORDERS_BENCHMARK            \
                                   \
    Max##A = Interval##A;          \
  }

   static void       OrderSend_Benchmark(const ulong &Interval1, const ulong &Interval2)
     {
#ifdef MT4ORDERS_BENCHMARK
      TMP_MT4ORDERS_BENCHMARK(1)
      TMP_MT4ORDERS_BENCHMARK(2)
#endif // MT4ORDERS_BENCHMARK

      return;
     }

#undef TMP_MT4ORDERS_BENCHMARK

   static string     ToString(const MqlTradeRequest &Request)
     {
      return(TOSTR2(Request.action) + TOSTR(Request.magic) + TOSTR(Request.order) +
             TOSTR(Request.symbol) + TOSTR(Request.volume) + TOSTR(Request.price) +
             TOSTR(Request.stoplimit) + TOSTR(Request.sl) +  TOSTR(Request.tp) +
             TOSTR(Request.deviation) + TOSTR2(Request.type) + TOSTR2(Request.type_filling) +
             TOSTR2(Request.type_time) + TOSTR(Request.expiration) + TOSTR(Request.comment) +
             TOSTR(Request.position) + TOSTR(Request.position_by));
     }

   static string     ToString(const MqlTradeResult &Result)
     {
      return(TOSTR(Result.retcode) + TOSTR(Result.deal) + TOSTR(Result.order) +
             TOSTR(Result.volume) + TOSTR(Result.price) + TOSTR(Result.bid) +
             TOSTR(Result.ask) + TOSTR(Result.comment) + TOSTR(Result.request_id) +
             TOSTR(Result.retcode_external));
     }

   static bool       OrderSend(const MqlTradeRequest &Request, MqlTradeResult &Result)
     {
      const bool FlagCalc = !MT4ORDERS::IsTester && MT4ORDERS::OrderSend_MaxPause;

      MqlTick PrevTick = {};

      if(FlagCalc)
         ::SymbolInfoTick(Request.symbol, PrevTick); // May slow down.

      const long PrevTimeCurrent = FlagCalc ? _B2(MT4ORDERS::GetTimeCurrent()) : 0;
      const ulong StartTime1 = FlagCalc ? ::GetMicrosecondCount() : 0;

      bool Res = ::OrderSend(Request, Result);

      const ulong StartTime2 = FlagCalc ? ::GetMicrosecondCount() : 0;

      const ulong Interval1 = StartTime2 - StartTime1;

      if(FlagCalc && Res && (Result.retcode < TRADE_RETCODE_ERROR))
        {
         Res = (Result.retcode == TRADE_RETCODE_DONE);
         MT4ORDERS::Waiting(true);

         // TRADE_ACTION_CLOSE_BY is not present in the list of checks
         if(Request.action == TRADE_ACTION_DEAL)
           {
            if(!Result.deal)
              {
               WHILE(_B2(::OrderSelect(Result.order)) || _B2(MT4ORDERS::HistorySelectOrder(Result.order)))
               ;

               if(!Res)
                  ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(::OrderSelect(Result.order)) + TOSTR(MT4ORDERS::HistorySelectOrder(Result.order)));
               else
                  if(::OrderSelect(Result.order) && !(Res = ((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE) == ORDER_STATE_PLACED) ||
                                                      ((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE) == ORDER_STATE_PARTIAL)))
                     ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(::OrderSelect(Result.order)) + TOSTR2((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE)));
              }

            // If the remaining part is still hanging after the partial execution, false.
            if(Res)
              {
               const bool ResultDeal = (!Result.deal) && (!MT4ORDERS::OrderSendBug);

               if(MT4ORDERS::OrderSendBug && (!Result.deal))
                  ::Print("Line = " + (string)__LINE__ + "\n" + "Before ::HistoryOrderSelect(Result.order):\n" + TOSTR(MT4ORDERS::OrderSendBug) + TOSTR(Result.deal));

               WHILE(_B2(MT4ORDERS::HistorySelectOrder(Result.order)))
               ;

               // If there was no OrderSend bug and there was Result.deal == 0
               if(ResultDeal)
                  MT4ORDERS::OrderSendBug = 0;

               if(!Res)
                  ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(MT4ORDERS::HistorySelectOrder(Result.order)) +
                          TOSTR(MT4ORDERS::HistorySelectDeal(Result.deal)) + TOSTR(::OrderSelect(Result.order)) + TOSTR(Result.deal));
               // If the historical order was not executed (due to rejection), false
               else
                  if(!(Res = ((ENUM_ORDER_STATE)::HistoryOrderGetInteger(Result.order, ORDER_STATE) == ORDER_STATE_FILLED) ||
                             ((ENUM_ORDER_STATE)::HistoryOrderGetInteger(Result.order, ORDER_STATE) == ORDER_STATE_PARTIAL)))
                     ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR2((ENUM_ORDER_STATE)::HistoryOrderGetInteger(Result.order, ORDER_STATE)));
              }

            if(Res)
              {
               const bool ResultDeal = (!Result.deal) && (!MT4ORDERS::OrderSendBug);

               if(MT4ORDERS::OrderSendBug && (!Result.deal))
                  ::Print("Line = " + (string)__LINE__ + "\n" + "Before MT4ORDERS::HistoryDealSelect(Result):\n" + TOSTR(MT4ORDERS::OrderSendBug) + TOSTR(Result.deal));

               WHILE(MT4ORDERS::HistoryDealSelect2(Result))
               ;

               // If there was no OrderSend bug and there was Result.deal == 0
               if(ResultDeal)
                  MT4ORDERS::OrderSendBug = 0;

               if(!Res)
                  ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(MT4ORDERS::HistoryDealSelect2(Result)));
              }
           }
         else
            if(Request.action == TRADE_ACTION_PENDING)
              {
               if(Res)
                 {
                  WHILE(_B2(::OrderSelect(Result.order)))
                  ;

                  if(!Res)
                     ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(::OrderSelect(Result.order)));
                  else
                     if(!(Res = ((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE) == ORDER_STATE_PLACED) ||
                                ((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE) == ORDER_STATE_PARTIAL)))
                        ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR2((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE)));
                 }
               else
                 {
                  WHILE(_B2(MT4ORDERS::HistorySelectOrder(Result.order)))
                  ;

                  ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(MT4ORDERS::HistorySelectOrder(Result.order)));

                  Res = false;
                 }
              }
            else
               if(Request.action == TRADE_ACTION_SLTP)
                 {
                  if(Res)
                    {
                     const int digits = (int)::SymbolInfoInteger(Request.symbol, SYMBOL_DIGITS);

                     bool EqualSL = false;
                     bool EqualTP = false;

                     do
                        if(Request.position ? _B2(::PositionSelectByTicket(Request.position)) : _B2(::PositionSelect(Request.symbol)))
                          {
                           EqualSL = MT4ORDERS::EqualPrices(::PositionGetDouble(POSITION_SL), Request.sl, digits);
                           EqualTP = MT4ORDERS::EqualPrices(::PositionGetDouble(POSITION_TP), Request.tp, digits);
                          }
                     WHILE(EqualSL && EqualTP);

                     if(!Res)
                        ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(::PositionGetDouble(POSITION_SL)) + TOSTR(::PositionGetDouble(POSITION_TP)) +
                                TOSTR(EqualSL) + TOSTR(EqualTP) +
                                TOSTR(Request.position ? ::PositionSelectByTicket(Request.position) : ::PositionSelect(Request.symbol)));
                    }
                 }
               else
                  if(Request.action == TRADE_ACTION_MODIFY)
                    {
                     if(Res)
                       {
                        const int digits = (int)::SymbolInfoInteger(Request.symbol, SYMBOL_DIGITS);

                        bool EqualSL = false;
                        bool EqualTP = false;
                        bool EqualPrice = false;

                        do
                           // https://www.mql5.com/ru/forum/170952/page184#comment_17913645
                           if(_B2(::OrderSelect(Result.order)) && ((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE) != ORDER_STATE_REQUEST_MODIFY))
                             {
                              EqualSL = MT4ORDERS::EqualPrices(::OrderGetDouble(ORDER_SL), Request.sl, digits);
                              EqualTP = MT4ORDERS::EqualPrices(::OrderGetDouble(ORDER_TP), Request.tp, digits);
                              EqualPrice = MT4ORDERS::EqualPrices(::OrderGetDouble(ORDER_PRICE_OPEN), Request.price, digits);
                             }
                        WHILE((EqualSL && EqualTP && EqualPrice));

                        if(!Res)
                           ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(::OrderGetDouble(ORDER_SL)) + TOSTR(Request.sl)+
                                   TOSTR(::OrderGetDouble(ORDER_TP)) + TOSTR(Request.tp) +
                                   TOSTR(::OrderGetDouble(ORDER_PRICE_OPEN)) + TOSTR(Request.price) +
                                   TOSTR(EqualSL) + TOSTR(EqualTP) + TOSTR(EqualPrice) +
                                   TOSTR(::OrderSelect(Result.order)) +
                                   TOSTR2((ENUM_ORDER_STATE)::OrderGetInteger(ORDER_STATE)));
                       }
                    }
                  else
                     if(Request.action == TRADE_ACTION_REMOVE)
                       {
                        if(Res)
                           WHILE(_B2(MT4ORDERS::HistorySelectOrder(Result.order)))
                           ;

                        if(!Res)
                           ::Print("Line = " + (string)__LINE__ + "\n" + TOSTR(MT4ORDERS::HistorySelectOrder(Result.order)));
                       }

         const ulong Interval2 = ::GetMicrosecondCount() - StartTime2;

         Result.comment += " " + ::DoubleToString(Interval1 / 1000.0, 3) + " + " +
                           ::DoubleToString(Interval2 / 1000.0, 3) + " (" + (string)MT4ORDERS::OrderSendBug + ") ms.";

         if(!Res || MT4ORDERS::OrderSendBug)
           {
            //::Alert(Res ? "OrderSend(" + (string)Result.order + ") - BUG!" : "MT4ORDERS - not Sync with History!");
            MT4ORDERS::AlertLog();

            ::Print(__FILE__ + "\nVersion = " + __MT4ORDERS__ + "\nCompiler = " + (string)__MQLBUILD__ + "\n" + TOSTR(__DATE__) +
                    TOSTR(::AccountInfoString(ACCOUNT_SERVER)) + TOSTR2((ENUM_ACCOUNT_TRADE_MODE)::AccountInfoInteger(ACCOUNT_TRADE_MODE)) +
                    TOSTR((bool)::TerminalInfoInteger(TERMINAL_CONNECTED)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_PING_LAST)) + TOSTR(::TerminalInfoDouble(TERMINAL_RETRANSMISSION)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_BUILD)) + TOSTR((bool)::TerminalInfoInteger(TERMINAL_X64)) +
                    TOSTR((bool)::TerminalInfoInteger(TERMINAL_VPS)) + TOSTR2((ENUM_PROGRAM_TYPE)::MQLInfoInteger(MQL_PROGRAM_TYPE)) +
                    TOSTR(::TimeCurrent()) + TOSTR(::TimeTradeServer()) +
                    TOSTR(MT4ORDERS::TimeToString(MT4ORDERS::GetTimeCurrent())) + TOSTR(MT4ORDERS::TimeToString(PrevTimeCurrent)) +
                    "PrevTick =" + MT4ORDERS::TickToString(Request.symbol, PrevTick) + "\n" +
                    "CurrentTick =" + MT4ORDERS::TickToString(Request.symbol) + "\n" +
                    TOSTR(::SymbolInfoString(Request.symbol, SYMBOL_PATH)) + TOSTR(::SymbolInfoString(Request.symbol, SYMBOL_DESCRIPTION)) +
                    TOSTR(::PositionsTotal()) + TOSTR(::OrdersTotal()) +
                    TOSTR(::HistorySelect(0, INT_MAX)) + TOSTR(::HistoryDealsTotal()) + TOSTR(::HistoryOrdersTotal()) +
                    (::HistoryDealsTotal() ? TOSTR(::HistoryDealGetTicket(::HistoryDealsTotal() - 1)) +
                     "DEAL_ORDER = " + (string)::HistoryDealGetInteger(::HistoryDealGetTicket(::HistoryDealsTotal() - 1), DEAL_ORDER) + "\n"
                     "DEAL_TIME_MSC = " + MT4ORDERS::TimeToString(::HistoryDealGetInteger(::HistoryDealGetTicket(::HistoryDealsTotal() - 1), DEAL_TIME_MSC)) + "\n"
                     : NULL) +
                    (::HistoryOrdersTotal() ? TOSTR(::HistoryOrderGetTicket(::HistoryOrdersTotal() - 1)) +
                     "ORDER_TIME_DONE_MSC = " + MT4ORDERS::TimeToString(::HistoryOrderGetInteger(::HistoryOrderGetTicket(::HistoryOrdersTotal() - 1), ORDER_TIME_DONE_MSC)) + "\n"
                     : NULL) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_AVAILABLE)) + TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_PHYSICAL)) +
                    TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_TOTAL)) + TOSTR(::TerminalInfoInteger(TERMINAL_MEMORY_USED)) +
                    TOSTR(::MQLInfoInteger(MQL_MEMORY_LIMIT)) + TOSTR(::MQLInfoInteger(MQL_MEMORY_USED)) +
                    TOSTR(MT4ORDERS::IsHedging) + TOSTR(Res) + TOSTR(MT4ORDERS::OrderSendBug) +
                    MT4ORDERS::ToString(Request) + MT4ORDERS::ToString(Result) +
#ifdef MT4ORDERS_BYPASS_MAXTIME
                    "MT4ORDERS::ByPass: " + MT4ORDERS::ByPass.ToString() + "\n" +
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME
                    TOSTR(MT4ORDERS::OrderSend_MaxPause));
           }
         else
            MT4ORDERS::OrderSend_Benchmark(Interval1, Interval2);
        }
      else
         if(FlagCalc)
           {
            Result.comment += " " + ::DoubleToString(Interval1 / 1000.0, 3) + " ms";

            ::Print(TOSTR(::TimeCurrent()) + TOSTR(::TimeTradeServer()) + TOSTR(MT4ORDERS::TimeToString(PrevTimeCurrent)) +
                    MT4ORDERS::TickToString(Request.symbol, PrevTick) + "\n" + MT4ORDERS::TickToString(Request.symbol) + "\n" +
                    MT4ORDERS::ToString(Request) + MT4ORDERS::ToString(Result));

            //      ExpertRemove();
           }

      return(Res);
     }

#undef TOSTR2
#undef TOSTR
#undef WHILE

   static ENUM_DAY_OF_WEEK GetDayOfWeek(const datetime &time)
     {
      MqlDateTime sTime = {};

      ::TimeToStruct(time, sTime);

      return((ENUM_DAY_OF_WEEK)sTime.day_of_week);
     }

   static bool       SessionTrade(const string &Symb)
     {
      datetime TimeNow = ::TimeCurrent();

      const ENUM_DAY_OF_WEEK DayOfWeek = MT4ORDERS::GetDayOfWeek(TimeNow);

      TimeNow %= 24 * 60 * 60;

      bool Res = false;
      datetime From, To;

      for(int i = 0; (!Res) && ::SymbolInfoSessionTrade(Symb, DayOfWeek, i, From, To); i++)
         Res = ((From <= TimeNow) && (TimeNow < To));

      return(Res);
     }

   static bool       SymbolTrade(const string &Symb)
     {
      MqlTick Tick;

      return(::SymbolInfoTick(Symb, Tick) ? (Tick.bid && Tick.ask && MT4ORDERS::SessionTrade(Symb) /* &&
           ((ENUM_SYMBOL_TRADE_MODE)::SymbolInfoInteger(Symb, SYMBOL_TRADE_MODE) == SYMBOL_TRADE_MODE_FULL) */) : false);
     }

   static bool       CorrectResult(void)
     {
      ::ZeroMemory(MT4ORDERS::LastTradeResult);

      MT4ORDERS::LastTradeResult.retcode = MT4ORDERS::LastTradeCheckResult.retcode;
      MT4ORDERS::LastTradeResult.comment = MT4ORDERS::LastTradeCheckResult.comment;

      return(false);
     }

   static bool       NewOrderCheck(void)
     {
      return((::OrderCheck(MT4ORDERS::LastTradeRequest, MT4ORDERS::LastTradeCheckResult) &&
              (MT4ORDERS::IsTester || MT4ORDERS::SymbolTrade(MT4ORDERS::LastTradeRequest.symbol))) ||
             (!MT4ORDERS::IsTester && MT4ORDERS::CorrectResult()));
     }

   static bool       NewOrderSend(const color &Check)
     {
      return((Check == INT_MAX) ? MT4ORDERS::NewOrderCheck() :
             (((Check != INT_MIN) || MT4ORDERS::NewOrderCheck()) && MT4ORDERS::OrderSend(MT4ORDERS::LastTradeRequest, MT4ORDERS::LastTradeResult)
              ? (MT4ORDERS::LastTradeResult.retcode < TRADE_RETCODE_ERROR)
#ifdef MT4ORDERS_BYPASS_MAXTIME
              && _B2(MT4ORDERS::ByPass += MT4ORDERS::LastTradeResult.order)
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME
              : false));
     }

   static bool       ModifyPosition(const long &Ticket, MqlTradeRequest &Request)
     {
      const bool Res = _B2(::PositionSelectByTicket(Ticket));

      if(Res)
        {
         Request.action = TRADE_ACTION_SLTP;

         Request.position = Ticket;
         Request.symbol = ::PositionGetString(POSITION_SYMBOL); // specifying a single ticket is not sufficient!
        }

      return(Res);
     }

   static ENUM_ORDER_TYPE_FILLING GetFilling(const string &Symb, const uint Type = ORDER_FILLING_FOK)
     {
      static ENUM_ORDER_TYPE_FILLING Res = ORDER_FILLING_FOK;
      static string LastSymb = NULL;
      static uint LastType = ORDER_FILLING_FOK;

      const bool SymbFlag = (LastSymb != Symb);

      if(SymbFlag || (LastType != Type))  // It can be lightly accelerated by changing the sequence of checking the condition.
        {
         LastType = Type;

         if(SymbFlag)
            LastSymb = Symb;

         const ENUM_SYMBOL_TRADE_EXECUTION ExeMode = (ENUM_SYMBOL_TRADE_EXECUTION)::SymbolInfoInteger(Symb, SYMBOL_TRADE_EXEMODE);
         const int FillingMode = (int)::SymbolInfoInteger(Symb, SYMBOL_FILLING_MODE);

         Res = (!FillingMode || (Type >= ORDER_FILLING_RETURN) || ((FillingMode & (Type + 1)) != Type + 1)) ?
               (((ExeMode == SYMBOL_TRADE_EXECUTION_EXCHANGE) || (ExeMode == SYMBOL_TRADE_EXECUTION_INSTANT)) ?
                ORDER_FILLING_RETURN : ((FillingMode == SYMBOL_FILLING_IOC) ? ORDER_FILLING_IOC : ORDER_FILLING_FOK)) :
               (ENUM_ORDER_TYPE_FILLING)Type;
        }

      return(Res);
     }

   static ENUM_ORDER_TYPE_TIME GetExpirationType(const string &Symb, uint Expiration = ORDER_TIME_GTC)
     {
      static ENUM_ORDER_TYPE_TIME Res = ORDER_TIME_GTC;
      static string LastSymb = NULL;
      static uint LastExpiration = ORDER_TIME_GTC;

      const bool SymbFlag = (LastSymb != Symb);

      if((LastExpiration != Expiration) || SymbFlag)
        {
         LastExpiration = Expiration;

         if(SymbFlag)
            LastSymb = Symb;

         const int ExpirationMode = (int)::SymbolInfoInteger(Symb, SYMBOL_EXPIRATION_MODE);

         if((Expiration > ORDER_TIME_SPECIFIED_DAY) || (!((ExpirationMode >> Expiration) & 1)))
           {
            if((Expiration < ORDER_TIME_SPECIFIED) || (ExpirationMode < SYMBOL_EXPIRATION_SPECIFIED))
               Expiration = ORDER_TIME_GTC;
            else
               if(Expiration > ORDER_TIME_DAY)
                  Expiration = ORDER_TIME_SPECIFIED;

            uint i = 1 << Expiration;

            while((Expiration <= ORDER_TIME_SPECIFIED_DAY) && ((ExpirationMode & i) != i))
              {
               i <<= 1;
               Expiration++;
              }
           }

         Res = (ENUM_ORDER_TYPE_TIME)Expiration;
        }

      return(Res);
     }

   static bool       ModifyOrder(const long Ticket, const double &Price, const datetime &Expiration, MqlTradeRequest &Request)
     {
      const bool Res = _B2(::OrderSelect(Ticket));

      if(Res)
        {
         Request.action = TRADE_ACTION_MODIFY;
         Request.order = Ticket;

         Request.price = Price;

         Request.symbol = ::OrderGetString(ORDER_SYMBOL);

         // https://www.mql5.com/ru/forum/1111/page1817#comment_4087275
         //      Request.type_filling = (ENUM_ORDER_TYPE_FILLING)::OrderGetInteger(ORDER_TYPE_FILLING);
         Request.type_filling = _B2(MT4ORDERS::GetFilling(Request.symbol));
         Request.type_time = _B2(MT4ORDERS::GetExpirationType(Request.symbol, (uint)Expiration));

         if(Expiration > ORDER_TIME_DAY)
            Request.expiration = Expiration;
        }

      return(Res);
     }

   static bool       SelectByPosHistory(const uint Index)
     {
      const ulong Ticket = MT4ORDERS::History[Index];
      const bool Res = (Ticket > 0) ? _B2(MT4ORDERS::HistorySelectDeal(Ticket)) : ((Ticket < 0) && _B2(MT4ORDERS::HistorySelectOrder(Ticket)));

      if(Res)
        {
         if(Ticket > 0)
            _BV2(MT4ORDERS::GetHistoryPositionData(Ticket))
            else
               _BV2(MT4ORDERS::GetHistoryOrderData(Ticket))
              }

      return(Res);
     }

   // https://www.mql5.com/ru/forum/227960#comment_6603506
   static bool       OrderVisible(void)
     {
      // if the position has closed while there is still a live partially filled pending order from which the position originated,
      // and the remaining part of the pending order was fully filled then but has not disappeared yet,
      // then we will see both the new position (correct) and the non-disappeared pending order (wrong).

      const ulong PositionID = ::OrderGetInteger(ORDER_POSITION_ID);
      const ENUM_ORDER_TYPE Type = (ENUM_ORDER_TYPE)::OrderGetInteger(ORDER_TYPE);
      ulong Ticket = 0;

      return(!((Type == ORDER_TYPE_CLOSE_BY) ||
               (PositionID && // Partial pending order has a non-zero PositionID.
                (Type <= ORDER_TYPE_SELL) && // Ignore closing market orders
                ((Ticket = ::OrderGetInteger(ORDER_TICKET)) != PositionID))) && // Do not ignor partially filled market orders.
             // Opening/position increasing order may not have time to disappear.
             (!::PositionsTotal() || !(::PositionSelectByTicket(Ticket ? Ticket : ::OrderGetInteger(ORDER_TICKET)) &&
                                       //                                     (::PositionGetInteger(POSITION_TYPE) == (::OrderGetInteger(ORDER_TYPE) & 1)) &&
                                       //                                     (::PositionGetInteger(POSITION_TIME_MSC) >= ::OrderGetInteger(ORDER_TIME_SETUP_MSC)) &&
                                       (::PositionGetDouble(POSITION_VOLUME) == ::OrderGetDouble(ORDER_VOLUME_INITIAL)))));
     }

   static ulong      OrderGetTicket(const int Index)
     {
      ulong Res;
      int PrevTotal;
      const long PrevTicket = ::OrderGetInteger(ORDER_TICKET);
      const long PositionTicket = ::PositionGetInteger(POSITION_TICKET);

      do
        {
         Res = 0;
         PrevTotal = ::OrdersTotal();

         if((Index >= 0) && (Index < PrevTotal))
           {
            int Count = 0;

            for(int i = 0; i < PrevTotal; i++)
              {
               const int Total = ::OrdersTotal();

               // Number of orders may change while searching for
               if(Total != PrevTotal)
                 {
                  PrevTotal = Total;

                  Count = 0;
                  i = -1;
                 }
               else
                 {
                  const ulong Ticket = ::OrderGetTicket(i);

                  if(Ticket && MT4ORDERS::OrderVisible())
                    {
                     if(Count == Index)
                       {
                        Res = Ticket;

                        break;
                       }

                     Count++;
                    }
                 }
              }
           }
        }
      while(
         /*           #ifdef MT4ORDERS_BYPASS_MAXTIME
                      _B2(MT4ORDERS::ByPass.Waiting()) &&
                    #endif // #ifdef MT4ORDERS_BYPASS_MAXTIME */
         (PrevTotal != ::OrdersTotal())); // Number of orders may change while searching

      // In case of a failure, select the order that have been chosen earlier.
      if(!Res && PrevTicket && (::OrderGetInteger(ORDER_TICKET) != PrevTicket))
         const bool AntiWarning = _B2(::OrderSelect(PrevTicket));

      // MT4ORDERS::OrderVisible() changes the position selection.
      if(PositionTicket && (::PositionGetInteger(POSITION_TICKET) != PositionTicket))
         ::PositionSelectByTicket(PositionTicket);

      return(Res);
     }

   // With the same tickets, the priority of position selection is higher than order selection
   static bool       SelectByPos(const int Index)
     {
      bool Flag = (Index == INT_MAX);
      bool Res = Flag || (Index == INT_MIN);

      if(!Res)
        {
         const int Total = ::PositionsTotal();

         Flag = (Index < Total);
         Res = Flag ? _B2(::PositionGetTicket(Index)) :
#ifdef MT4ORDERS_SELECTFILTER_OFF
               ::OrderGetTicket(Index - Total);
#else // MT4ORDERS_SELECTFILTER_OFF
               (MT4ORDERS::IsTester ? ::OrderGetTicket(Index - Total) : _B2(MT4ORDERS::OrderGetTicket(Index - Total)));
#endif //MT4ORDERS_SELECTFILTER_OFF
        }

      if(Res)
        {
         if(Flag)
            MT4ORDERS::GetPositionData(); // (Index == INT_MAX) - switch to an MT5 position without checking the existence and updating.
         else
            MT4ORDERS::GetOrderData();    // (Index == INT_MIN) - switch to a live MT5 order without checking the existence and updating.
        }

      return(Res);
     }

   static bool       SelectByHistoryTicket(const ulong &Ticket)
     {
      bool Res = false;

      if(!Ticket)  // Selection by OrderTicketID (by zero value - balance operations).
        {
         const ulong TicketDealOut = MT4ORDERS::History.GetPositionDealOut(Ticket);

         if(Res = _B2(MT4ORDERS::HistorySelectDeal(TicketDealOut)))
            _BV2(MT4ORDERS::GetHistoryPositionData(TicketDealOut));
        }
      else
         if(_B2(MT4ORDERS::HistorySelectDeal(Ticket)))
           {
#ifdef MT4ORDERS_TESTER_SELECT_BY_TICKET
            // In the tester, when searching for a closed position, we must first search by PositionID due to a close numbering of MT5 deals/orders.
            if(MT4ORDERS::IsTester)
              {
               const ulong TicketDealOut = MT4ORDERS::History.GetPositionDealOut(HistoryOrderGetInteger(Ticket, ORDER_POSITION_ID));

               if(Res = _B2(MT4ORDERS::HistorySelectDeal(TicketDealOut)))
                  _BV2(MT4ORDERS::GetHistoryPositionData(TicketDealOut));
              }

            if(!Res)
#endif // #ifdef MT4ORDERS_TESTER_SELECT_BY_TICKET
              {
               if(Res = MT4HISTORY::IsMT4Deal(Ticket))
                  _BV2(MT4ORDERS::GetHistoryPositionData(Ticket))
                  else// DealIn
                    {
                     const ulong TicketDealOut = MT4ORDERS::History.GetPositionDealOut(HistoryDealGetInteger(Ticket, DEAL_POSITION_ID)); // Select by DealIn

                     if(Res = _B2(MT4ORDERS::HistorySelectDeal(TicketDealOut)))
                        _BV2(MT4ORDERS::GetHistoryPositionData(TicketDealOut))
                       }
              }
           }
         else
            if(_B2(MT4ORDERS::HistorySelectOrder(Ticket)))
              {
               if(Res = MT4HISTORY::IsMT4Order(Ticket))
                  _BV2(MT4ORDERS::GetHistoryOrderData(Ticket))
                  else
                    {
                     const ulong TicketDealOut = MT4ORDERS::History.GetPositionDealOut(HistoryOrderGetInteger(Ticket, ORDER_POSITION_ID));

                     if(Res = _B2(MT4ORDERS::HistorySelectDeal(TicketDealOut)))
                        _BV2(MT4ORDERS::GetHistoryPositionData(TicketDealOut));
                    }
              }
            else
              {
               // Choosing by OrderTicketID or by the ticket of an executed pending order is relevant to Netting.
               const ulong TicketDealOut = MT4ORDERS::History.GetPositionDealOut(Ticket);

               if(Res = _B2(MT4ORDERS::HistorySelectDeal(TicketDealOut)))
                  _BV2(MT4ORDERS::GetHistoryPositionData(TicketDealOut));
              }

      return(Res);
     }

   static bool       SelectByExistingTicket(const ulong &Ticket)
     {
      bool Res = true;

      if(Ticket < 0)
        {
         if(_B2(::OrderSelect(Ticket)))
            MT4ORDERS::GetOrderData();
         else
            if(_B2(::PositionSelectByTicket(Ticket)))
               MT4ORDERS::GetPositionData();
            else
               Res = false;
        }
      else
         if(_B2(::PositionSelectByTicket(Ticket)))
            MT4ORDERS::GetPositionData();
         else
            if(_B2(::OrderSelect(Ticket)))
               MT4ORDERS::GetOrderData();
            else
               if(_B2(MT4ORDERS::HistorySelectDeal(Ticket)))
                 {
#ifdef MT4ORDERS_TESTER_SELECT_BY_TICKET
                  // In the tester, when searching for a closed position, we must first search by PositionID due to a close numbering of MT5 deals/orders.
                  if(Res = !MT4ORDERS::IsTester)
#endif // #ifdef MT4ORDERS_TESTER_SELECT_BY_TICKET
                    {
                     if(MT4HISTORY::IsMT4Deal(Ticket))  // If the choice is made by DealOut.
                        _BV2(MT4ORDERS::GetHistoryPositionData(Ticket))
                        else
                           if(_B2(::PositionSelectByTicket(::HistoryDealGetInteger(Ticket, DEAL_POSITION_ID))))  // Select by DealIn
                              MT4ORDERS::GetPositionData();
                           else
                              Res = false;
                    }
                 }
               else
                  if(_B2(MT4ORDERS::HistorySelectOrder(Ticket)) && _B2(::PositionSelectByTicket(::HistoryOrderGetInteger(Ticket, ORDER_POSITION_ID))))  // Select by MT5 order ticket
                     MT4ORDERS::GetPositionData();
                  else
                     Res = false;

      return(Res);
     }

   // With the same ticket, selection priorities are:
   // MODE_TRADES:  existing position > existing order > deal > canceled order
   // MODE_HISTORY: deal > canceled order > existing position > existing order
   static bool       SelectByTicket(const ulong &Ticket, const int &Pool)
     {
      return((Pool == MODE_TRADES) || (Ticket < 0) ?
             (_B2(MT4ORDERS::SelectByExistingTicket(Ticket)) || ((Ticket > 0) && _B2(MT4ORDERS::SelectByHistoryTicket(Ticket)))) :
             (_B2(MT4ORDERS::SelectByHistoryTicket(Ticket)) || _B2(MT4ORDERS::SelectByExistingTicket(Ticket))));
     }

#ifdef MT4ORDERS_SLTP_OLD
   static void       CheckPrices(double &MinPrice, double &MaxPrice, const double Min, const double Max)
     {
      if(MinPrice && (MinPrice >= Min))
         MinPrice = 0;

      if(MaxPrice && (MaxPrice <= Max))
         MaxPrice = 0;

      return;
     }
#endif // MT4ORDERS_SLTP_OLD

   static int        OrdersTotal(void)
     {
      int Res = 0;
      const long PrevTicket = ::OrderGetInteger(ORDER_TICKET);
      const long PositionTicket = ::PositionGetInteger(POSITION_TICKET);
      int PrevTotal;

      do
        {
         PrevTotal = ::OrdersTotal();

         for(int i = PrevTotal - 1; i >= 0; i--)
           {
            const int Total = ::OrdersTotal();

            // Number of orders may change while searching for
            if(Total != PrevTotal)
              {
               PrevTotal = Total;

               Res = 0;
               i = PrevTotal;
              }
            else
               if(::OrderGetTicket(i) && MT4ORDERS::OrderVisible())
                  Res++;
           }
        }
      while(PrevTotal != ::OrdersTotal());    // Number of orders may change while searching for

      if(PrevTicket && (::OrderGetInteger(ORDER_TICKET) != PrevTicket))
         const bool AntiWarning = _B2(::OrderSelect(PrevTicket));

      // MT4ORDERS::OrderVisible() changes the position selection.
      if(PositionTicket && (::PositionGetInteger(POSITION_TICKET) != PositionTicket))
         ::PositionSelectByTicket(PositionTicket);

      return(Res);
     }

public:
   static uint       OrderSend_MaxPause; // the maximum time for synchronization in microseconds.

#ifdef MT4ORDERS_BYPASS_MAXTIME
   static BYPASS     ByPass;
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

   static MqlTradeResult LastTradeResult;
   static MqlTradeRequest LastTradeRequest;
   static MqlTradeCheckResult LastTradeCheckResult;

   static bool       MT4OrderSelect(const ulong &Index, const int &Select, const int &Pool)
     {
      return(
#ifdef MT4ORDERS_BYPASS_MAXTIME
               (MT4ORDERS::IsTester || ((Select == SELECT_BY_POS) && ((Index == INT_MIN) || (Index == INT_MAX))) || _B2(MT4ORDERS::ByPass.Waiting())) &&
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME
               ((Select == SELECT_BY_POS) ?
                ((Pool == MODE_TRADES) ? _B2(MT4ORDERS::SelectByPos((int)Index)) : _B2(MT4ORDERS::SelectByPosHistory((int)Index))) :
                _B2(MT4ORDERS::SelectByTicket(Index, Pool))));
     }

   static int        MT4OrdersTotal(void)
     {
#ifdef MT4ORDERS_SELECTFILTER_OFF
      return(::OrdersTotal() + ::PositionsTotal());
#else // MT4ORDERS_SELECTFILTER_OFF
      int Res;

      if(MT4ORDERS::IsTester)
         return(::OrdersTotal() + ::PositionsTotal());
      else
        {
         int PrevTotal;

#ifdef MT4ORDERS_BYPASS_MAXTIME
         _B2(MT4ORDERS::ByPass.Waiting());
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

         do
           {
            PrevTotal = ::PositionsTotal();

            Res = _B2(MT4ORDERS::OrdersTotal()) + PrevTotal;

           }
         while(
            /*             #ifdef MT4ORDERS_BYPASS_MAXTIME
                           _B2(MT4ORDERS::ByPass.Waiting()) &&
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME  */
      (PrevTotal != ::PositionsTotal())); // Only position changes are tracked, since orders are tracked in MT4ORDERS::OrdersTotal()
     }

                     return(Res); // https://www.mql5.com/ru/forum/290673#comment_9493241
#endif //MT4ORDERS_SELECTFILTER_OFF
  }

// This "overload" also allows using the MT5 version of OrdersTotal
static int MT4OrdersTotal(const bool)
  {
   return(::OrdersTotal());
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static int MT4OrdersHistoryTotal(void)
  {
#ifdef MT4ORDERS_BYPASS_MAXTIME
   _B2(MT4ORDERS::ByPass.Waiting());
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

   return(MT4ORDERS::History.GetAmount());
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static long MT4OrderSend(const string &Symb, const int &Type, const double &dVolume, const double &Price, const int &SlipPage, const double &SL, const double &TP,
                         const string &comment, const MAGIC_TYPE &magic, const datetime &dExpiration, const color &arrow_color)

  {
   ::ZeroMemory(MT4ORDERS::LastTradeRequest);

   MT4ORDERS::LastTradeRequest.action = (((Type == OP_BUY) || (Type == OP_SELL)) ? TRADE_ACTION_DEAL : TRADE_ACTION_PENDING);
   MT4ORDERS::LastTradeRequest.magic = magic;

   MT4ORDERS::LastTradeRequest.symbol = ((Symb == NULL) ? ::Symbol() : Symb);
   MT4ORDERS::LastTradeRequest.volume = dVolume;
   MT4ORDERS::LastTradeRequest.price = Price;

   MT4ORDERS::LastTradeRequest.tp = TP;
   MT4ORDERS::LastTradeRequest.sl = SL;
   MT4ORDERS::LastTradeRequest.deviation = SlipPage;
   MT4ORDERS::LastTradeRequest.type = (ENUM_ORDER_TYPE)Type;

   MT4ORDERS::LastTradeRequest.type_filling = _B2(MT4ORDERS::GetFilling(MT4ORDERS::LastTradeRequest.symbol, (uint)MT4ORDERS::LastTradeRequest.deviation));

   if(MT4ORDERS::LastTradeRequest.action == TRADE_ACTION_PENDING)
     {
      MT4ORDERS::LastTradeRequest.type_time = _B2(MT4ORDERS::GetExpirationType(MT4ORDERS::LastTradeRequest.symbol, (uint)dExpiration));

      if(dExpiration > ORDER_TIME_DAY)
         MT4ORDERS::LastTradeRequest.expiration = dExpiration;
     }

   if(comment != NULL)
      MT4ORDERS::LastTradeRequest.comment = comment;

   return((arrow_color == INT_MAX) ? (MT4ORDERS::NewOrderCheck() ? 0 : -1) :
          ((((int)arrow_color != INT_MIN) || MT4ORDERS::NewOrderCheck()) &&
           MT4ORDERS::OrderSend(MT4ORDERS::LastTradeRequest, MT4ORDERS::LastTradeResult)
#ifdef MT4ORDERS_BYPASS_MAXTIME
           && (!MT4ORDERS::IsHedging || _B2(MT4ORDERS::ByPass += MT4ORDERS::LastTradeResult.order))
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME
           ?
           (MT4ORDERS::IsHedging ? (long)MT4ORDERS::LastTradeResult.order : // PositionID == Result.order - a feature of MT5-Hedge
            ((MT4ORDERS::LastTradeRequest.action == TRADE_ACTION_DEAL) ?
             (MT4ORDERS::IsTester ? (_B2(::PositionSelect(MT4ORDERS::LastTradeRequest.symbol)) ? PositionGetInteger(POSITION_TICKET) : 0) :
// HistoryDealSelect в MT4ORDERS::OrderSend
              ::HistoryDealGetInteger(MT4ORDERS::LastTradeResult.deal, DEAL_POSITION_ID)) :
             (long)MT4ORDERS::LastTradeResult.order)) : -1));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static bool MT4OrderModify(const long &Ticket, const double &Price, const double &SL, const double &TP, const datetime &Expiration, const color &Arrow_Color)
  {
   ::ZeroMemory(MT4ORDERS::LastTradeRequest);

// Considers the case when an order and a position with the same ticket are present
   bool Res = (Ticket < 0) ? MT4ORDERS::ModifyOrder(-Ticket, Price, Expiration, MT4ORDERS::LastTradeRequest) :
              ((MT4ORDERS::Order.Ticket != ORDER_SELECT) ?
               (MT4ORDERS::ModifyPosition(Ticket, MT4ORDERS::LastTradeRequest) || MT4ORDERS::ModifyOrder(Ticket, Price, Expiration, MT4ORDERS::LastTradeRequest)) :
               (MT4ORDERS::ModifyOrder(Ticket, Price, Expiration, MT4ORDERS::LastTradeRequest) || MT4ORDERS::ModifyPosition(Ticket, MT4ORDERS::LastTradeRequest)));

//    if (Res) // Ignore the check - OrderCheck is present
     {
      MT4ORDERS::LastTradeRequest.tp = TP;
      MT4ORDERS::LastTradeRequest.sl = SL;

      Res = MT4ORDERS::NewOrderSend(Arrow_Color);
     }

   return(Res);
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static bool MT4OrderClose(const long &Ticket, const double &dLots, const double &Price, const int &SlipPage, const color &Arrow_Color, const string &comment)
  {
// MT4ORDERS::LastTradeRequest and MT4ORDERS::LastTradeResult are present, therefore the result is not affected. However, it is necessary for PositionGetString below
   _B2(::PositionSelectByTicket(Ticket));

   ::ZeroMemory(MT4ORDERS::LastTradeRequest);

   MT4ORDERS::LastTradeRequest.action = TRADE_ACTION_DEAL;
   MT4ORDERS::LastTradeRequest.position = Ticket;

   MT4ORDERS::LastTradeRequest.symbol = ::PositionGetString(POSITION_SYMBOL);

// Save the comment when partially closing the position
//    if (dLots < ::PositionGetDouble(POSITION_VOLUME))
   MT4ORDERS::LastTradeRequest.comment = (comment == NULL) ? ::PositionGetString(POSITION_COMMENT) : comment;

// Is it correct not to define magic number when closing? -It is!
   MT4ORDERS::LastTradeRequest.volume = dLots;
   MT4ORDERS::LastTradeRequest.price = Price;

#ifdef MT4ORDERS_SLTP_OLD
// Needed to determine the SL/TP levels of the closed position. Inverted - not an error
// SYMBOL_SESSION_PRICE_LIMIT_MIN and SYMBOL_SESSION_PRICE_LIMIT_MAX do not need any validation, since the initial SL/TP have already been set
   MT4ORDERS::LastTradeRequest.tp = ::PositionGetDouble(POSITION_SL);
   MT4ORDERS::LastTradeRequest.sl = ::PositionGetDouble(POSITION_TP);

   if(MT4ORDERS::LastTradeRequest.tp || MT4ORDERS::LastTradeRequest.sl)
     {
      const double StopLevel = ::SymbolInfoInteger(MT4ORDERS::LastTradeRequest.symbol, SYMBOL_TRADE_STOPS_LEVEL) *
                               ::SymbolInfoDouble(MT4ORDERS::LastTradeRequest.symbol, SYMBOL_POINT);

      const bool FlagBuy = (::PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
      const double CurrentPrice = SymbolInfoDouble(MT4ORDERS::LastTradeRequest.symbol, FlagBuy ? SYMBOL_ASK : SYMBOL_BID);

      if(CurrentPrice)
        {
         if(FlagBuy)
            MT4ORDERS::CheckPrices(MT4ORDERS::LastTradeRequest.tp, MT4ORDERS::LastTradeRequest.sl, CurrentPrice - StopLevel, CurrentPrice + StopLevel);
         else
            MT4ORDERS::CheckPrices(MT4ORDERS::LastTradeRequest.sl, MT4ORDERS::LastTradeRequest.tp, CurrentPrice - StopLevel, CurrentPrice + StopLevel);
        }
      else
        {
         MT4ORDERS::LastTradeRequest.tp = 0;
         MT4ORDERS::LastTradeRequest.sl = 0;
        }
     }
#endif // MT4ORDERS_SLTP_OLD

   MT4ORDERS::LastTradeRequest.deviation = SlipPage;

   MT4ORDERS::LastTradeRequest.type = (ENUM_ORDER_TYPE)(1 - ::PositionGetInteger(POSITION_TYPE));

   MT4ORDERS::LastTradeRequest.type_filling = _B2(MT4ORDERS::GetFilling(MT4ORDERS::LastTradeRequest.symbol, (uint)MT4ORDERS::LastTradeRequest.deviation));

   return(MT4ORDERS::NewOrderSend(Arrow_Color));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static bool MT4OrderCloseBy(const long &Ticket, const long &Opposite, const color &Arrow_Color)
  {
   ::ZeroMemory(MT4ORDERS::LastTradeRequest);

   MT4ORDERS::LastTradeRequest.action = TRADE_ACTION_CLOSE_BY;
   MT4ORDERS::LastTradeRequest.position = Ticket;
   MT4ORDERS::LastTradeRequest.position_by = Opposite;

   if((!MT4ORDERS::IsTester) && _B2(::PositionSelectByTicket(Ticket)))  // needed for MT4ORDERS::SymbolTrade()
      MT4ORDERS::LastTradeRequest.symbol = ::PositionGetString(POSITION_SYMBOL);

   return(MT4ORDERS::NewOrderSend(Arrow_Color));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static bool MT4OrderDelete(const long &Ticket, const color &Arrow_Color)
  {
//    bool Res = ::OrderSelect(Ticket); // Is it necessary, when MT4ORDERS::LastTradeRequest and MT4ORDERS::LastTradeResult are needed?

   ::ZeroMemory(MT4ORDERS::LastTradeRequest);

   MT4ORDERS::LastTradeRequest.action = TRADE_ACTION_REMOVE;
   MT4ORDERS::LastTradeRequest.order = Ticket;

   if((!MT4ORDERS::IsTester) && _B2(::OrderSelect(Ticket)))  // needed for MT4ORDERS::SymbolTrade()
      MT4ORDERS::LastTradeRequest.symbol = ::OrderGetString(ORDER_SYMBOL);

   return(MT4ORDERS::NewOrderSend(Arrow_Color));
  }

#define MT4_ORDERFUNCTION(NAME,T,A,B,C)                               \
  static T MT4Order##NAME( void )                                     \
  {                                                                   \
    return(POSITION_ORDER((T)(A), (T)(B), MT4ORDERS::Order.NAME, C)); \
  }

#define POSITION_ORDER(A,B,C,D) (((MT4ORDERS::Order.Ticket == POSITION_SELECT) && (D)) ? (A) : ((MT4ORDERS::Order.Ticket == ORDER_SELECT) ? (B) : (C)))

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERFUNCTION(Ticket, long, ::PositionGetInteger(POSITION_TICKET), ::OrderGetInteger(ORDER_TICKET), true)
MT4_ORDERFUNCTION(Type, int, ::PositionGetInteger(POSITION_TYPE), ::OrderGetInteger(ORDER_TYPE), true)
MT4_ORDERFUNCTION(Lots, double, ::PositionGetDouble(POSITION_VOLUME), ::OrderGetDouble(ORDER_VOLUME_CURRENT), true)
MT4_ORDERFUNCTION(OpenPrice, double, ::PositionGetDouble(POSITION_PRICE_OPEN), (::OrderGetDouble(ORDER_PRICE_OPEN) ? ::OrderGetDouble(ORDER_PRICE_OPEN) : ::OrderGetDouble(ORDER_PRICE_CURRENT)), true)
MT4_ORDERFUNCTION(OpenTimeMsc, long, ::PositionGetInteger(POSITION_TIME_MSC), ::OrderGetInteger(ORDER_TIME_SETUP_MSC), true)
MT4_ORDERFUNCTION(OpenTime, datetime, ::PositionGetInteger(POSITION_TIME), ::OrderGetInteger(ORDER_TIME_SETUP), true)
MT4_ORDERFUNCTION(StopLoss, double, ::PositionGetDouble(POSITION_SL), ::OrderGetDouble(ORDER_SL), true)
MT4_ORDERFUNCTION(TakeProfit, double, ::PositionGetDouble(POSITION_TP), ::OrderGetDouble(ORDER_TP), true)
MT4_ORDERFUNCTION(ClosePrice, double, ::PositionGetDouble(POSITION_PRICE_CURRENT), ::OrderGetDouble(ORDER_PRICE_CURRENT), true)
MT4_ORDERFUNCTION(CloseTimeMsc, long, 0, 0, true)
MT4_ORDERFUNCTION(CloseTime, datetime, 0, 0, true)
MT4_ORDERFUNCTION(Expiration, datetime, 0, ::OrderGetInteger(ORDER_TIME_EXPIRATION), true)
MT4_ORDERFUNCTION(MagicNumber, long, ::PositionGetInteger(POSITION_MAGIC), ::OrderGetInteger(ORDER_MAGIC), true)
MT4_ORDERFUNCTION(Profit, double, ::PositionGetDouble(POSITION_PROFIT), 0, true)
MT4_ORDERFUNCTION(Swap, double, ::PositionGetDouble(POSITION_SWAP), 0, true)
MT4_ORDERFUNCTION(Symbol, string, ::PositionGetString(POSITION_SYMBOL), ::OrderGetString(ORDER_SYMBOL), true)
MT4_ORDERFUNCTION(Comment, string, MT4ORDERS::Order.Comment, ::OrderGetString(ORDER_COMMENT), MT4ORDERS::CheckPositionCommissionComment())
MT4_ORDERFUNCTION(Commission, double, MT4ORDERS::Order.Commission, 0, MT4ORDERS::CheckPositionCommissionComment())

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERFUNCTION(OpenPriceRequest, double, MT4ORDERS::Order.OpenPriceRequest, ::OrderGetDouble(ORDER_PRICE_OPEN), MT4ORDERS::CheckPositionOpenPriceRequest())
MT4_ORDERFUNCTION(ClosePriceRequest, double, ::PositionGetDouble(POSITION_PRICE_CURRENT), ::OrderGetDouble(ORDER_PRICE_CURRENT), true)

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERFUNCTION(TicketOpen, long, MT4ORDERS::Order.TicketOpen, ::OrderGetInteger(ORDER_TICKET), MT4ORDERS::CheckPositionTicketOpen())
//  MT4_ORDERFUNCTION(OpenReason, ENUM_DEAL_REASON, MT4ORDERS::Order.OpenReason, ::OrderGetInteger(ORDER_REASON), MT4ORDERS::CheckPositionOpenReason())
MT4_ORDERFUNCTION(OpenReason, ENUM_DEAL_REASON, ::PositionGetInteger(POSITION_REASON), ::OrderGetInteger(ORDER_REASON), true)
MT4_ORDERFUNCTION(CloseReason, ENUM_DEAL_REASON, 0, ::OrderGetInteger(ORDER_REASON), true)
MT4_ORDERFUNCTION(TicketID, long, ::PositionGetInteger(POSITION_IDENTIFIER), ::OrderGetInteger(ORDER_TICKET), true)

#undef POSITION_ORDER
#undef MT4_ORDERFUNCTION

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static void MT4OrderPrint(void)
  {
   if(MT4ORDERS::Order.Ticket == POSITION_SELECT)
      MT4ORDERS::CheckPositionCommissionComment();

   ::Print(MT4ORDERS::Order.ToString());

   return;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
static double MT4OrderLots(const bool&)
  {
   double Res = MT4ORDERS::MT4OrderLots();

   if(Res && (MT4ORDERS::Order.Ticket == POSITION_SELECT))
     {
      const ulong PositionID = ::PositionGetInteger(POSITION_IDENTIFIER);

      if(::PositionSelectByTicket(PositionID))
        {
         const int Type = 1 - (int)::PositionGetInteger(POSITION_TYPE);

         double PrevVolume = Res;
         double NewVolume = 0;

         while(Res && (NewVolume != PrevVolume))
           {
#ifdef MT4ORDERS_BYPASS_MAXTIME
            _B2(MT4ORDERS::ByPass.Waiting());
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

            if(::PositionSelectByTicket(PositionID))
              {
               Res = ::PositionGetDouble(POSITION_VOLUME);
               PrevVolume = Res;

               for(int i = ::OrdersTotal() - 1; i >= 0; i--)
                  if(!::OrderGetTicket(i))  // Happens if i == ::OrdersTotal() - 1.
                    {
                     PrevVolume = -1;

                     break;
                    }
                  else
                     if((::OrderGetInteger(ORDER_POSITION_ID) == PositionID) &&
                        (::OrderGetInteger(ORDER_TYPE) == Type))
                        Res -= ::OrderGetDouble(ORDER_VOLUME_CURRENT);


               if(::PositionSelectByTicket(PositionID))
                  NewVolume = ::PositionGetDouble(POSITION_VOLUME);
               else
                  Res = 0;
              }
           }
        }
      else
         Res = 0;
     }

   return(Res);
  }

#undef ORDER_SELECT
#undef POSITION_SELECT
  };

// #define OrderToString MT4ORDERS::MT4OrderToString

static MT4_ORDER MT4ORDERS::Order = {};

static MT4HISTORY MT4ORDERS::History;

static const bool MT4ORDERS::IsTester = ::MQLInfoInteger(MQL_TESTER);

// If you switch the account, this value will still be recalculated for EAs
// https://www.mql5.com/ru/forum/170952/page61#comment_6132824
static const bool MT4ORDERS::IsHedging = ((ENUM_ACCOUNT_MARGIN_MODE)::AccountInfoInteger(ACCOUNT_MARGIN_MODE) ==
      ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);

static int MT4ORDERS::OrderSendBug = 0;

static uint MT4ORDERS::OrderSend_MaxPause = 1000000; // the maximum time for synchronization in microseconds.

#ifdef MT4ORDERS_BYPASS_MAXTIME
static BYPASS MT4ORDERS::ByPass(MT4ORDERS_BYPASS_MAXTIME);
#endif // #ifdef MT4ORDERS_BYPASS_MAXTIME

static MqlTradeResult MT4ORDERS::LastTradeResult = {};
static MqlTradeRequest MT4ORDERS::LastTradeRequest = {};
static MqlTradeCheckResult MT4ORDERS::LastTradeCheckResult = {};

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool OrderClose(const long Ticket, const double dLots, const double Price, const int SlipPage, const color Arrow_Color = clrNONE, const string comment = NULL)
  {
   return(MT4ORDERS::MT4OrderClose(Ticket, dLots, Price, SlipPage, Arrow_Color, comment));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool OrderModify(const long Ticket, const double Price, const double SL, const double TP, const datetime Expiration, const color Arrow_Color = clrNONE)
  {
   return(MT4ORDERS::MT4OrderModify(Ticket, Price, SL, TP, Expiration, Arrow_Color));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool OrderCloseBy(const long Ticket, const long Opposite, const color Arrow_Color = clrNONE)
  {
   return(MT4ORDERS::MT4OrderCloseBy(Ticket, Opposite, Arrow_Color));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool OrderDelete(const long Ticket, const color Arrow_Color = clrNONE)
  {
   return(MT4ORDERS::MT4OrderDelete(Ticket, Arrow_Color));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OrderPrint(void)
  {
   MT4ORDERS::MT4OrderPrint();

   return;
  }

#define MT4_ORDERGLOBALFUNCTION(NAME,T)     \
  T Order##NAME( void )                     \
  {                                         \
    return((T)MT4ORDERS::MT4Order##NAME()); \
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERGLOBALFUNCTION(sHistoryTotal, int)
MT4_ORDERGLOBALFUNCTION(Ticket, TICKET_TYPE)
MT4_ORDERGLOBALFUNCTION(Type, int)
MT4_ORDERGLOBALFUNCTION(Lots, double)
MT4_ORDERGLOBALFUNCTION(OpenPrice, double)
MT4_ORDERGLOBALFUNCTION(OpenTimeMsc, long)
MT4_ORDERGLOBALFUNCTION(OpenTime, datetime)
MT4_ORDERGLOBALFUNCTION(StopLoss, double)
MT4_ORDERGLOBALFUNCTION(TakeProfit, double)
MT4_ORDERGLOBALFUNCTION(ClosePrice, double)
MT4_ORDERGLOBALFUNCTION(CloseTimeMsc, long)
MT4_ORDERGLOBALFUNCTION(CloseTime, datetime)
MT4_ORDERGLOBALFUNCTION(Expiration, datetime)
MT4_ORDERGLOBALFUNCTION(MagicNumber, MAGIC_TYPE)
MT4_ORDERGLOBALFUNCTION(Profit, double)
MT4_ORDERGLOBALFUNCTION(Commission, double)
MT4_ORDERGLOBALFUNCTION(Swap, double)
MT4_ORDERGLOBALFUNCTION(Symbol, string)
MT4_ORDERGLOBALFUNCTION(Comment, string)

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERGLOBALFUNCTION(OpenPriceRequest, double)
MT4_ORDERGLOBALFUNCTION(ClosePriceRequest, double)

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
MT4_ORDERGLOBALFUNCTION(TicketOpen, TICKET_TYPE)
MT4_ORDERGLOBALFUNCTION(OpenReason, ENUM_DEAL_REASON)
MT4_ORDERGLOBALFUNCTION(CloseReason, ENUM_DEAL_REASON)
MT4_ORDERGLOBALFUNCTION(TicketID, TICKET_TYPE)

#undef MT4_ORDERGLOBALFUNCTION

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double OrderLots(const bool Value)
  {
   return(MT4ORDERS::MT4OrderLots(Value));
  }

// Overloaded standard functions
#define OrdersTotal MT4ORDERS::MT4OrdersTotal // AFTER Expert/Expert.mqh - there is a call to MT5-OrdersTotal()

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool OrderSelect(const ulong Index, const int Select, const int Pool = MODE_TRADES)
  {
   return(_B2(MT4ORDERS::MT4OrderSelect(Index, Select, Pool)));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
TICKET_TYPE OrderSend(const string Symb, const int Type, const double dVolume, const double Price, const int SlipPage, const double SL, const double TP,
                      const string comment = NULL, const MAGIC_TYPE magic = 0, const datetime dExpiration = 0, color arrow_color = clrNONE)
  {
   return((TICKET_TYPE)MT4ORDERS::MT4OrderSend(Symb, Type, dVolume, Price, SlipPage, SL, TP, comment, magic, dExpiration, arrow_color));
  }

#define RETURN_ASYNC(A) return((A) && ::OrderSendAsync(MT4ORDERS::LastTradeRequest, MT4ORDERS::LastTradeResult) &&                        \
                               (MT4ORDERS::LastTradeResult.retcode == TRADE_RETCODE_PLACED) ? MT4ORDERS::LastTradeResult.request_id : 0);

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
uint OrderCloseAsync(const long Ticket, const double dLots, const double Price, const int SlipPage, const color Arrow_Color = clrNONE)
  {
   RETURN_ASYNC(OrderClose(Ticket, dLots, Price, SlipPage, INT_MAX))
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
uint OrderModifyAsync(const long Ticket, const double Price, const double SL, const double TP, const datetime Expiration, const color Arrow_Color = clrNONE)
  {
   RETURN_ASYNC(OrderModify(Ticket, Price, SL, TP, Expiration, INT_MAX))
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
uint OrderDeleteAsync(const long Ticket, const color Arrow_Color = clrNONE)
  {
   RETURN_ASYNC(OrderDelete(Ticket, INT_MAX))
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
uint OrderSendAsync(const string Symb, const int Type, const double dVolume, const double Price, const int SlipPage, const double SL, const double TP,
                    const string comment = NULL, const MAGIC_TYPE magic = 0, const datetime dExpiration = 0, color arrow_color = clrNONE)
  {
   RETURN_ASYNC(!OrderSend(Symb, Type, dVolume, Price, SlipPage, SL, TP, comment, magic, dExpiration, INT_MAX))
  }

#undef RETURN_ASYNC

#undef MT4ORDERS_SLTP_OLD

#undef _BV2
#undef _B3
#undef _B2

#ifdef MT4ORDERS_BENCHMARK_MINTIME
#undef MT4ORDERS_BENCHMARK_MINTIME
#endif // MT4ORDERS_BENCHMARK_MINTIME

// #undef TICKET_TYPE
#endif // __MT4ORDERS__
#else  // __MQL5__
#define TICKET_TYPE int
#define MAGIC_TYPE  int

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
TICKET_TYPE OrderTicketID(void) { return(::OrderTicket()); }
#endif // _


//+------------------------------------------------------------------+
//|                                                        ST EA.mq5 |
//|                                  Copyright 2024, MetaQuotes Ltd. |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Copyright 2024, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "1.14"
#property strict
#include <Trade/Trade.mqh>
CTrade Trade;
CPositionInfo PositionsInfo;


input bool CommanderCheck = true;//Commander Check

//=== COC Dashboard Integration ===
input group "🎛️ COC Dashboard Settings"
input bool Enable_COC_Dashboard = true;        // Enable COC Dashboard Integration
input string COC_Backend_URL = "http://127.0.0.1:80"; // COC Backend API URL
input string COC_Instance_UUID = "";           // Instance UUID (auto-generated if empty)
input string COC_Strategy_Tag = "BOC_Range_Breakout";    // Strategy identification tag
input int COC_Status_Update_Interval = 30;     // Status update interval in seconds
input int COC_Command_Check_Interval = 10;     // Command check interval in seconds
input bool COC_Enable_Remote_Control = true;   // Allow remote control from dashboard
input bool COC_Auto_Export_Data = true;        // Auto export data to JSON files
input string COC_Data_Path = "MQL5\\Files\\COC_Data\\"; // Data export path
input group "Strategy Settings Regime 1"
input bool Enable_Trading_Regime_1   =  true;//Enable Trading Regime 1
//input int pendingOrderExpiryCandles = 3;

input string EA_Name = "Range_Breakout_EA";
input int eamagic = 42313; //Magic Number
input bool Show_Dashboard = true;
input int Dashboard_Update_Seconds = 5;
input bool Show_Debug_Logic = true; // Enables Confluence & Volatility display
//----------------------------------------------------------------------------------------------------------------------//
//---------------------------------------------- New Conditions --------------------------------------------------------//
input string S_0 = "=============================================( ->   Breakout Candle  <-)==========================================";
input ENUM_TIMEFRAMES Default_Candle_TimeFrame = PERIOD_H4;//Default Candle TimeFrame
enum sel_000
  {
   High_Low,//High/Low
   Open_Close,//Open/Close
  };
input sel_000 Prior_Candles = High_Low;//Prior Candles
input int Number_Of_Prior_Candles_To_Check  = 1;//Number of Prior Candles to Check
input double Price_Buffer_Percentage = 0.2;
input int BreakOut_Validity_Candles = 1;
input bool Strict_BreakOut_Entry = true;//Strict BreakOut Entry


enum ord_types
  {
   o_limit, //Limit Order
   o_stop, //Stop Order
   o_both //Both
  };



struct virtual_tp_struct
  {
   ulong             tck;
   double            tp_level;
   double            sl_level;
   double            open_level;
   bool              pclosed;
  };
virtual_tp_struct tp_levels[];

enum trade_modes
  {
   buy_only, //Buy Only
   sell_only, //Sell Only
   both //Both
  };


input group "Lot Calculation Method"
input double fixlot = 0.1; //Fixed Lots
input bool use_dynamic_lots = true; //Use Dynamic Lots
input double trade_risk_money = 50; //Risked Money $
input double MaxCapLotSize = 20;//Maximum Cap Lot Size









input group "Multiple Trade Logic Regime 1";
bool Allow_Multiple_Trades_On_Same_Candle = false;
bool Allow_Entry_on_Other_Candle_While_This_Trade_is_Open = false;
bool Allow_Only_On_Different_SuperTrend = false;

input int Maximum_No_Of_Trades_Simultenously = 2;
input int Maximum_No_Of_Trades_On_BO_Cand = 2;//Maximum No Of Trades On Brakount Candle


input group "Risk Management Section Regime 1"
double TrailingStopOrderBufferPercentage = 0.2;//Minimum Trailing Stop Order Buffer %
double Trailing_ATR_Multiplier = 2;//Trailing ATR Multiplier SDST


input double max_atrpct_1 = 0.1; //Max SL %
input double min_atrpct_1 = 0.08; //Min SL %
input double tp_mult_1 = 7; //TP Multiplier (R:R)
double SL_ATR_Filter_Multiplier = tp_mult_1;
input bool Use_Structure_SL_Filter = true;//Use Structure SL Filter
input int SL_Candle_Count  = 3;//SL Candle Count
//input string Structure_TF_List = "M15,M30,H1,H4";//Structure TF List
input ENUM_TIMEFRAMES  Structure_Candle_TF_From = PERIOD_M15;//Structure Candle TF From
input ENUM_TIMEFRAMES  Structure_Candle_TF_To = PERIOD_H4;//Structure Candle TF To

ENUM_TIMEFRAMES TFs_List[] =
  {
   PERIOD_M1,
   PERIOD_M2,
   PERIOD_M3,
   PERIOD_M4,
   PERIOD_M5,
   PERIOD_M6,
   PERIOD_M10,
   PERIOD_M12,
   PERIOD_M15,
   PERIOD_M20,
   PERIOD_M30,
   PERIOD_H1,
   PERIOD_H2,
   PERIOD_H3,
   PERIOD_H4,
   PERIOD_H6,
   PERIOD_H8,
   PERIOD_H12,
   PERIOD_D1,
   PERIOD_W1,
   PERIOD_MN1,
  };



input double SL_Structure_Buffer_Percent = 0.1;//SL Structure Buffer Percent
input bool Journal_Structure_SL = true;//Journal Structure SL





//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
input group "Volatility Regime Filter (ATR%)"
input bool Use_Primary_ATR = true;//Use Primary ATR Filter
input double Minimum_ATR_Percentage = 0.3;//Primary Minimum ATR %
input double Maximum_ATR_Percentage= 0.5;//Primary Maximum ATR %
input ENUM_TIMEFRAMES ATRFilterTF = PERIOD_H4;//Primary ATR  TimeFrame
input int ATRFilterPeriod = 14;//Primary ATR  Period
int Hndl_ATR_SL;
double ATR_SL[];

input bool Enable_Higher_TF_ATR_Filter = true;//Enable Higher TF ATR Filter
input double Higher_TF_Min_ATR_Percent  = 0.61;//Higher TF Min ATR Percent
input double Higher_TF_Max_ATR_Percent  = 1.60;//Higher TF Max ATR Percent
input int Higher_TF_ATR_Period  = 14;//Higher TF ATR Period
input ENUM_TIMEFRAMES Higher_TF_ATR_Timeframe = PERIOD_D1;//Higher TF ATR Timeframe

int Hndl_ATR_Filter_HTF;
double ATR_Filter_HTF[];








input group "Trailing and Breakeven Settings"
input string TBE_1 = "==== ATR Perc OvreRide Trail ====";
input bool ATR_Perc_OvreRide_Trail = true;//ATR% Override For Trailing
input double ATR_Perc_OvreRide_MultiPlier_ = 1.5;//ATR% Limit Multiplier For Override
double ATR_Perc_OvreRide_MultiPlier = ATR_Perc_OvreRide_MultiPlier_;
input ENUM_TIMEFRAMES ATR_Perc_OverRide_TF = PERIOD_D1;//ATR% Override TimeFrame
input ENUM_TIMEFRAMES ATR_Perc_OverRide_Trailing_Stop_TF = PERIOD_M15;//Trailing Stop TimeFreme Override
input double ATR_Perc_OverRide_Buffer_Perc_Pre = 0.2;//Trailing Stop ATR% Buffer PreTrailing
input double ATR_Perc_OverRide_Candle_Perc_Post = 0.2;//Trailing Stop ATR% Buffer PostTrailing
input double ATR_Perc_OverRide_Price_Perc_Post = 0.2;//Trailing Stop ATR% Buffer PostTrailing
int Hndl_ATR_PERC_OverRide;
double ATR_PERC_OverRide[];


input string TBE_2 = "==== Pre Trailing ====";
input bool Use_Pre_Trailing = true; //Use Trailing Stop Pre-TP
input double Trailing_Pre_tp_mult_1 = 2; //Trailing Stop Start Multiplier
input double Trailing_Pre_Buffer_Percentage = 0; //Trailing Stop Buffer % Pre-TP
input ENUM_TIMEFRAMES Trailing_Pre_TF = PERIOD_M15; //Trailing Stop Timeframe Pre-TP


input bool Check_Prior_Candles_For_Pre_TP_Trailing  = true;//Check No of Prior Candles For Pre-TP Trailing
input int No_Of_Prior_Cands = 3;//No Of Prior Candles To Check
input double ATR_PERC_Multipler_Buffer = 0.15;//ATR % Multiplier Buffer
input ENUM_TIMEFRAMES TimeFrame_For_Checking = PERIOD_CURRENT;//TimeFrame For Checking

input string TBE_3 = "==== BreakEven ====";
input bool Use_BreakEven = true; //Use Breakeven
input double BE_Trigger_Multiplier = 2; //Breakeven Trigger Multiplier
input double BE_Offset_Multiplier = 0.01; //Breakeven Offset Multiplier

enum sel_1
  {
   Cand_Green,//Green
   Cand_Red,//Red
   Cand_Any,//Any
  };
enum sel_4
{
 Trigger_On_Cross,//Trigger On Cross
 Trigger_On_Close,//Trigger On Close
};
enum sel_5
{
 Trail_By_Candle,//Trail By Candle
 Trail_By_Percent,//Trail By Percent
};  
input string TBE_4 = "==== Bollinger Band Trailing ====";
input bool Use_BB_Trailing = true;
input sel_4 BB_Trail_Method = Trigger_On_Close;//BB Trail Method
input sel_5 BB_Trail_Type = Trail_By_Candle;//BB Trail Type
input ENUM_TIMEFRAMES BB_Trailing_TF = PERIOD_D1;
input int BB_Trailing_Period = 16;
input ENUM_APPLIED_PRICE BB_Applied_Price = PRICE_CLOSE;
input double BB_Deviation = 2;
input sel_1 BB_Trailing_Cnd_Col = Cand_Any;
input ENUM_TIMEFRAMES BB_Trailing_Cnd_TF = PERIOD_H1;
input double BB_Trailing_Min_SL_Mult_ = 1.4;
double BB_Trailing_Min_SL_Mult = BB_Trailing_Min_SL_Mult_;
input double BB_Trailing_Candle_Percentage = 0.1;
input double BB_Trailing_Price_Percentage = 0.1;
input bool Journal_BB_Trailing = true;

int Hndl_BB_Trail;
double BB_Trail_UP[];
double BB_Trail_DN[];


input string TBE_5 = "==== RSI Trailing Logic ====";
input bool Use_RSI_Trailing = true;
input sel_4 RSI_Trail_Method = Trigger_On_Close;//RSI Trail Method
input sel_5 RSI_Trail_Type = Trail_By_Candle;//RSI Trail Type
input ENUM_TIMEFRAMES RSI_Trailing_TF = PERIOD_D1;
input int  RSI_Trailing_Period = 14;
input double RSI_Trailing_Threshold_Long  = 70;
input double RSI_Trailing_Threshold_Short = 30;
input sel_1 RSI_Trailing_Cnd_Col = Cand_Any;
input ENUM_TIMEFRAMES RSI_Trailing_Cnd_TF = PERIOD_H1;
input double RSI_Trailing_Min_SL_Mult_ = 1.4;
double RSI_Trailing_Min_SL_Mult = RSI_Trailing_Min_SL_Mult_;
input double RSI_Trailing_Candle_Percentage = 0.1;
input double RSI_Trailing_Price_Percentage = 0.1;
input bool Journal_RSI_Trailing = true;
int Hndl_RSI_Trail;
double RSI_Trail_Buffer[];




input string TBE_6 = "==== ATR% Structure-Based Trailing====";
enum sel_2
  {
   HighLow,
   OpenCloseMax,//OpenClose
  };
enum sel_3
  {
   OnClose,//Close
   OnCross,//Cross
  };
input bool ATR_Trailing_Override_Enabled = true;
input double ATR_Trailing_Override_Multiplier = 1.6;
input ENUM_TIMEFRAMES ATR_Trailing_Override_Timeframe = PERIOD_H4;
input sel_2 ATR_Trailing_PriceCross_Type = HighLow;
input int ATR_Trailing_Candle_Count = 3;
input sel_3 ATR_Trailing_Trigger_Method = OnClose;
input ENUM_TIMEFRAMES Trailing_Stop_Candle_TF = PERIOD_M15;
input sel_1 Trailing_Stop_Candle_Colour = Cand_Any;
input double Trailing_Stop_ATR_Buffer_Percentage = 0.1;
input double Trailing_Stop_Min_SL_Multiplier_ = 1.4;
double Trailing_Stop_Min_SL_Multiplier = Trailing_Stop_Min_SL_Multiplier_;
input bool Journal_ATR_Trailing_Override = true;




input string TBE_7 = "==== Post Take-Profit Trailing ====";
input bool Use_Post_Trailing = true;
input sel_4 Post_Trail_Method = Trigger_On_Close;//Post Trail Method
input sel_5 Post_Trail_Type = Trail_By_Candle;//Post Trail Type
input double Trailing_Post_Candle_Percentage = 0.1;
input double Trailing_Post_Price_Percentage = 0.1;
input ENUM_TIMEFRAMES Trailing_Post_TF = PERIOD_M12;
input sel_1 Trailing_Post_Candle_Colour = Cand_Any;
input bool Journal_Post_Trailing = true;



input bool Use_PostTP_InsideBar_Exit  = true;//Use PostTP InsideBar Exit
input ENUM_TIMEFRAMES Price_Structure_TF = PERIOD_H4;//Price Structure TF
input int Compression_Candle_Count  = 2;//Compression Candle Count
input double Compression_Buffer_Percentage = 0.1;//Compression Buffer Percentage

input string TBE_8 = "==== Candle-Based BreakEven(SL Multiplier Protected) ====";
input bool Enable_Candle_Structure_BE   = true;//Enable Candle Structure BE
input ENUM_TIMEFRAMES Candle_BE_Timeframe = PERIOD_H1;//Candle BE Timeframe  
input int Candle_BE_Lookback_Count =   3;//Candle BE Lookback Count
input double Candle_BE_Close_Above_Buffer_Percent = 0.1;//Candle BE Close Above Buffer Percent
input double Candle_BE_SL_Buffer_Percent  =  0.1;//Candle BE SL Buffer Percent
input bool Use_Min_BE_Distance_Filter =  true;//Use Min BE Distance Filter
input double Min_BE_Distance_Multiplier =  1.2;//Min BE Distance Multiplier
input bool Journal_Candle_BE_Logic = true;//Journal Candle BE Logic
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
input string TBE_9 = "==== Add-On Trade Module (SL-in-Profit Entry) ===="; 
input bool Enable_AddOn_Trade = true;//Enable AddOn Trade
input string TBE_90 = "+______Entry Conditions______+";//+-----Entry Conditions 
input double SL_Profit_Trigger_Multiplier = 0.05;//SL Profit Trigger Multiplier
input double AddOn_Trigger_At_RR_Multiple = 2;//AddOn Trigger At RR Multiple
input double AddOn_Entry_Buffer_Percent = 0.1;//AddOn Entry Buffer Percent
input int AddOn_Cancel_Hours = 4;//AddOn Cancel Hours
input int  AddOn_Max_Attempts = 1;//AddOn Max Attempts
input string TBE_91 = "+______Position Size______+";//+-----Position Size
input double AddOn_Risk_Multiplier = 0.5;//AddOn Risk Multiplier
input string TBE_92 = "+______TP Settings______+";//+-----TP Settings
input double AddOn_Use_Own_TP = true;//AddOn Use Own TP
input double AddOn_TP_Multiplier = 1.5;//AddOn TP Multiplier
input string TBE_93 = "+______Trailing Settings______+";//+-----Trailing Settings
input bool AddOn_Use_Own_Trailing = true;//AddOn Use Own Trailing
enum sel_6{
Percent,//Percent
Candle_Logic,//Candle Logic
};
enum sel_7{
GreenCand,//Green
RedCand,//Red
};
input sel_5 AddOn_Trailing_Mode = Trail_By_Candle;//AddOn Trailing Mode
input double AddOn_Trailing_Buffer = 0.2;//AddOn Trailing Buffer
input ENUM_TIMEFRAMES AddOn_Trailing_TF = PERIOD_H1;//AddOn Trailing TF
input sel_1 AddOn_Trailing_Candle_Color = Cand_Any;//AddOn Trailing Candle Color
input string TBE_95 = "+______Journal Control______+";//+-----Journal Control
input bool AddOn_Journal_Enabled = true;//AddOn Journal Enabled












enum sel_0
  {
   Cross,
   Just_Close,
  };


input group " Candle Range Logic"
input bool Enable_CandleRange_Logic = true;//Enable CandleRange Logic
input bool Enable_Range_Journal = true;//Enable Range Journal
input ENUM_TIMEFRAMES Candle_1_TimeFrame =  PERIOD_D1;//Candle 1 TimeFrame
input ENUM_TIMEFRAMES Candle_2_TimeFrame =  PERIOD_W1;//Candle 2 TimeFrame

input string S_2222_0 = "-----> Compression Mode C1 Inside C2 Inside <-----";//+--Compression Mode C1 Inside C2 Inside--+
input bool   Enable_Compression_Mode_C1_C2 = true;//Enable_Compression_Mode_C1_Inside_C2_Inside
input double Risked_Money_Multiplier_Compression = 0.8;//Risked_Money Multiplier
input double TP_Multiplier_Compression = 1;//TP_Multiplier
input double ATR_Percentage_Override_Multiplier_Compression = 1;//ATR%_Override_Multiplier
input double BB_Trailing_Min_SL_Multiplier_Compression = 0.8;//BB_Trailing_Min_SL_Multiplier
input double RSI_Trailing_Min_SL_Multiplier_Compression = 0.8;//RSI_Trailing_Min_SL_Multiplier
input double Structure_SL_Multiplier_Compression   = 0.9;//ATR%_Structure_Trailing_Min_SL_Multiplier



input string S_2222_1 = "-----> Mixed Mode C2 Inside C1 Outside <-----";//+--Mixed Mode C2 Inside C1 Outside--+
input bool   Enable_Mixed_Mode_C2_Inside_C1_Outside = true;//Enable_Mixed_Mode_C2_Inside_C1_Outside
input double Risked_Money_Multiplier_Mixed_C2_In_C1_Out = 0.9;//Risked_Money Multiplier
input double TP_Multiplier_Mixed_C2_In_C1_Out  = 1.1;//TP_Multiplier
input double ATR_Percentage_Override_Multiplier_Mixed_C2_In_C1_Out  = 1.1;//ATR%_Override_Multiplier
input double BB_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out  = 1.0;//BB_Trailing_Min_SL_Multiplier
input double RSI_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out  = 1.0;//RSI_Trailing_Min_SL_Multiplier
input double Structure_SL_Multiplier_Mixed_C2_In_C1_Out    = 1.0;//ATR%_Structure_Trailing_Min_SL_Multiplier


input string S_2222_2 = "-----> Mixed Mode C2 Outside C1 Inside <-----";//+--Mixed Mode C2 Outside C1 Inside--+
input bool   Enable_Mixed_Mode_C2_Outside_C1_Inside = true;//Enable_Mixed_Mode_C2_Outside_C1_Inside
input double Risked_Money_Multiplier_Mixed_C2_Out_C1_In = 1.1;//Risked_Money Multiplier
input double TP_Multiplier_Mixed_C2_Out_C1_In = 1.1;//TP_Multiplier
input double ATR_Percentage_Override_Multiplier_Mixed_C2_Out_C1_In = 1.1;//ATR%_Override_Multiplier
input double BB_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In = 1.1;//BB_Trailing_Min_SL_Multiplier
input double RSI_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In = 1.1;//RSI_Trailing_Min_SL_Multiplier
input double Structure_SL_Multiplier_Mixed_C2_Out_C1_In   = 1.0;//ATR%_Structure_Trailing_Min_SL_Multiplier

input string S_2222_3 = "-----> Expansion Mode C1 Outside C2 Outside<-----";//+--Expansion Mode C1 Outside C2 Outside--+
input bool   Enable_Expansion_Mode_C1_C2 = true;//Enable_Expansion_Mode_C1_Outside_C2_Outside
input double Risked_Money_Multiplier_Expansion = 1.2;//Risked_Money Multiplier
input double TP_Multiplier_Expansion = 1.2;//TP_Multiplier
input double ATR_Percentage_Override_Multiplier_Expansion = 1.2;//ATR%_Override_Multiplier
input double BB_Trailing_Min_SL_Multiplier_Expansion = 1.2;//BB_Trailing_Min_SL_Multiplier
input double RSI_Trailing_Min_SL_Multiplier_Expansion = 1.2;//RSI_Trailing_Min_SL_Multiplier
input double Structure_SL_Multiplier_Expansion  = 1.2;//ATR%_Structure_Trailing_Min_SL_Multiplier







input group "Other Trade Management Settings"
input trade_modes trademode = buy_only; //Trade Direction Mode


input group "Execution Settings"
input ENUM_TIMEFRAMES exec_tf = PERIOD_CURRENT; //Executing Timeframe

input group "Multi-TimeFrame Indicators Settings"
input bool use_basema1 = false; //Use MA 1
input ENUM_TIMEFRAMES basema1_tf = PERIOD_D1; //MA 1 Timeframe
input int basema1_p = 200; //MA 1 Period
input ENUM_MA_METHOD basema1_mode = MODE_SMA; //MA 1 Mode
input ENUM_APPLIED_PRICE basema1_price = PRICE_CLOSE; //MA 1 Price
input bool basema1_reverse = false; //MA 1 Reversed
input bool use_basema3 = false; //Use MA 2
input ENUM_TIMEFRAMES basema3_tf = PERIOD_D1; //MA 2 Timeframe
input int basema3_p = 200; //MA 2 Period
input ENUM_MA_METHOD basema3_mode = MODE_SMA; //MA 2 Mode
input ENUM_APPLIED_PRICE basema3_price = PRICE_CLOSE; //MA 2 Price
input bool basema3_reverse = false; //MA 2 Reversed

input bool use_basema4 = false; //Use MA 3
input ENUM_TIMEFRAMES basema4_tf = PERIOD_D1; //MA 3 Timeframe
input int basema4_p = 200; //MA 3 Period
input ENUM_MA_METHOD basema4_mode = MODE_SMA; //MA 3 Mode
input ENUM_APPLIED_PRICE basema4_price = PRICE_CLOSE; //MA 3 Price
input bool basema4_reverse = false; //MA 3 Reversed

input bool use_basema2 = false; //Use SuperTrend
input ENUM_TIMEFRAMES basema2_tf = PERIOD_D1; //SuperTrend Timeframe
input int basema2_p = 10; //SuperTrend Period
input double basema2_m = 2.5; //SuperTrend Multiplier
input bool basema2_reverse = false; //SuperTrend Reversed


input bool use_basema5 = false; //Use SuperTrend 2
input ENUM_TIMEFRAMES basema5_tf = PERIOD_D1; //SuperTrend 2 Timeframe
input int basema5_p = 10; //SuperTrend 2 Period
input double basema5_m = 2.5; //SuperTrend 2 Multiplier
input bool basema5_reverse = false; //SuperTrend 2 Reversed




input group "Confluence Settings Regime  1"
input bool Enable_Confluence_Master = true;//Enable Confluence Master
input bool Confluence_Enable_Journal = true;//Confluence Enable Journal
input int Confluence_Optional_Minimum_Pass = 1;//Confluence Optional Minimum Pass
input string N0 = "//------------------------------------ RSI 1-------------------------------------//";//--------- RSI 1---------
input bool  Regime1_Use_RSI_Confluence_1 = true;//Regime1 Use RSI Confluence 1
input bool  Regime1_RSI_Confluence_1_Mandatory = true;//Regime1 RSI Confluence 1 Mandatory
input ENUM_TIMEFRAMES Regime1_RSI_TimeFrame_1 = PERIOD_H4;//Regime1RSI Timeframe 1
input int  Regime1_RSI_Period_1 = 14;//Regime1 RSI Period 1
input ENUM_APPLIED_PRICE Regime1_RSI_Price_1 = PRICE_CLOSE;//Regime1 RSI Price 1
input double  Regime1_RSI_Minimum_Level_1 = 40;//Regime1 RSI Minimum Level 1
input double  Regime1_RSI_Maximum_Level_1= 75;//Regime1 RSI Maximum Level 1
int Hndl_Regime1_RSI_1;
double Regime1_RSI_1[];

input string N1 = "//------------------------------------ RSI 2-------------------------------------//";//--------- RSI 2---------
input bool  Regime1_Use_RSI_Confluence_2 = true;//Regime1 Use RSI Confluence 2
input bool  Regime1_RSI_Confluence_2_Mandatory = false;//Regime1 RSI Confluence 2 Mandatory
input ENUM_TIMEFRAMES Regime1_RSI_TimeFrame_2 = PERIOD_H4;//Regime1RSI Timeframe 2
input int  Regime1_RSI_Period_2 = 14;//Regime1 RSI Period 2
input ENUM_APPLIED_PRICE Regime1_RSI_Price_2 = PRICE_CLOSE;//Regime1 RSI Price 2
input double  Regime1_RSI_Minimum_Level_2 = 40;//Regime1 RSI Minimum Level 2
input double  Regime1_RSI_Maximum_Level_2 = 75;//Regime1 RSI Maximum Level 2
int Hndl_Regime1_RSI_2;
double Regime1_RSI_2[];

input string N2 = "//------------------------------------ ADX 1-------------------------------------//";//--------- ADX 1---------
input bool  Regime1_Use_ADX_Confluence_1 = true;//Regime1 Use ADX Confluence 1
input bool  Regime1_ADX_Confluence_1_Mandatory = true;//Regime1 ADX Confluence 1 Mandatory
input ENUM_TIMEFRAMES Regime1_ADX_Timeframe_1 = PERIOD_H4;//Regime1 ADX Timeframe 1
input int  Regime1_ADX_Period_1 = 14;//Regime1 ADX Period 1
input double  Regime1_ADX_Minimum_Level_1 = 20;//Regime1 ADX Minimum Level 1
input double  Regime1_ADX_Maximum_Level_1 = 50;//Regime1 ADX Maximum Level 1
int Hndl_Regime1_ADX_1;
double Regime1_ADX_1[];


//------------------------------------ ADX MA 1 -------------------------------------//
input bool Regime1_Use_ADX_MA_Smoothing_1 = true;//Regime1 Use ADX MA Smoothing
//input bool Regime1_Use_ADX_MA_Smoothing_1_Mandatory = true;//Regime1 ADX MA Smoothing 1 Mandatory
input ENUM_MA_METHOD Regime1_ADX_MA_Type_1 = MODE_EMA;//Regime1 ADX MA Type
input int Regime1_ADX_MA_Period_1 = 7;//Regime1 ADX MA Period
int Regime1_Hndl_MA_ADX_1;
double Regime1_MA_ADX_1[];



input string N3 = "//------------------------------------ ADX 2-------------------------------------//";//--------- ADX 2---------
input bool  Regime1_Use_ADX_Confluence_2 = true;//Regime1 Use ADX Confluence 2
input bool  Regime1_ADX_Confluence_2_Mandatory = false;//Regime1 ADX Confluence 2 Mandatory
input ENUM_TIMEFRAMES Regime1_ADX_Timeframe_2 = PERIOD_H4;//Regime1 ADX Timeframe 2
input int  Regime1_ADX_Period_2 = 14;//Regime1 ADX Period 2
input double  Regime1_ADX_Minimum_Level_2 = 20;//Regime1 ADX Minimum Level 2
input double  Regime1_ADX_Maximum_Level_2 = 50;//Regime1 ADX Maximum Level 2
int Hndl_Regime1_ADX_2;
double Regime1_ADX_2[];

//------------------------------------ ADX MA 2 -------------------------------------//
input bool Regime1_Use_ADX_MA_Smoothing_2 = true;//Regime1 Use ADX MA Smoothing
//input bool Regime1_Use_ADX_MA_Smoothing_2_Mandatory = true;//Regime1 ADX MA Smoothing 2 Mandatory
input ENUM_MA_METHOD Regime1_ADX_MA_Type_2 = MODE_EMA;//Regime1 ADX MA Type
input int Regime1_ADX_MA_Period_2 = 7;//Regime1 ADX MA Period
int Regime1_Hndl_MA_ADX_2;
double Regime1_MA_ADX_2[];






input group "Strength Comparison Settings Regime 1"
input bool Enable_Comparison_Master = true;//Enable Strength Comparison Master
input bool Comparison_Enable_Journal = true;//Strength Comparison Enable Journal
input int Comparison_Optional_Minimum_Pass = 1;//Strength Comparison Optional Minimum Pass
input string comp_symbol = "USTEC"; //Comparison Symbol

input string N11 =  "//------------------------------------ Comp MA  -------------------------------------//";//----- Comp MA  -----
input bool Check_comp_ma = false; // Compare MA
input bool comp_ma_Mandatory = true;//Comp MA Mandatory
input ENUM_TIMEFRAMES comp_ma_tf = PERIOD_D1; //MA Timeframe
input int comp_ma_p = 200; //MA Period
input ENUM_MA_METHOD comp_ma_mode = MODE_SMA; //MA Mode
input ENUM_APPLIED_PRICE comp_ma_price = PRICE_CLOSE; //MA Price
input bool comp_ma_reverse = false; // MA Reverse

input string N12 =  "//------------------------------------ Comp ST -------------------------------------//";//----- Comp ST  -----
input bool Check_comp_st = false; // Compare SuperTrend
input bool comp_st_Mandatory = true;//Comp ST Mandatory
input ENUM_TIMEFRAMES comp_st_tf = PERIOD_D1; //SuperTrend Timeframe
input int comp_st_p = 10; //SuperTrend Period
input double comp_st_m = 2.5; //SuperTrend Multiplier
input bool comp_st_reverse = false; // ST Reverse

input string N13 =  "//------------------------------------ Comp RSI 1 -------------------------------------//";//----- Comp RSI 1  -----
input bool Check_comp_rsi_1 = true; // Compare RSI Threshold 1
input bool comp_rsi_1_Mandatory = true;//Comp RSI 1 Mandatory
input ENUM_TIMEFRAMES RSI_Comp_TF_1 = PERIOD_CURRENT; // RSI Timeframe  1
input int RSI_Period_Comp_1 = 14; // RSI Period 1
input ENUM_APPLIED_PRICE RSI_Comp_AppliedPrice_1 = PRICE_CLOSE; // RSI Applied Price 1
input double  RSI_Comp_Minimum_Level_1 = 40;//Compare RSI Minimum Level 1
input double  RSI_Comp_Maximum_Level_1 = 75;//Compare RSI Maximum Level 1

input string N14 =  "//------------------------------------ Comp RSI 2 -------------------------------------//";//----- Comp RSI 2  -----
input bool Check_comp_rsi_2 = true; // Compare RSI Threshold 2
input bool comp_rsi_2_Mandatory = true;//Comp RSI 2 Mandatory
input ENUM_TIMEFRAMES RSI_Comp_TF_2 = PERIOD_CURRENT; // RSI Timeframe  2
input int RSI_Period_Comp_2 = 14; // RSI Period 2
input ENUM_APPLIED_PRICE RSI_Comp_AppliedPrice_2 = PRICE_CLOSE; // RSI Applied Price 2
input double  RSI_Comp_Minimum_Level_2 = 40;//Compare RSI Minimum Level 2
input double  RSI_Comp_Maximum_Level_2 = 75;//Compare RSI Maximum Level 2

input string N15 =  "//------------------------------------ Comp ADX 1-------------------------------------//";//----- Comp ADX 1  -----
input bool  Comp_Use_ADX_1 = true;//Compare Use ADX Confluence 1
input bool Comp_adx_1_Mandatory = true;//Comp ADX 1 Mandatory
input ENUM_TIMEFRAMES Comp_ADX_Timeframe_1 = PERIOD_H4;//Compare Regime1 ADX Timeframe 1
input int  Comp_ADX_Period_1 = 14;//Compare Regime1 ADX Period 1
input double  Comp_ADX_Minimum_Level_1 = 20;//Compare Regime1 ADX Minimum Level 1
input double  Comp_ADX_Maximum_Level_1 = 50;//Compare Regime1 ADX Maximum Level 1
int Hndl_Comp_ADX_1;
double Comp_ADX_1[];

input bool Comp_Use_ADX_MA_Smoothing_1 = true;//Compare Use ADX MA Smoothing
input ENUM_MA_METHOD Comp_ADX_MA_Type_1 = MODE_EMA;//Compare ADX MA Type
input int Comp_ADX_MA_Period_1 = 7;//Compare ADX MA Period
int Comp_Hndl_MA_ADX_1;
double Comp_MA_ADX_1[];

input string N16 =  "//------------------------------------ Comp ADX 2-------------------------------------//";//----- Comp ADX 2  -----
input bool  Comp_Use_ADX_2 = true;//Compare Use ADX Confluence 2
input bool Comp_adx_2_Mandatory = true;//Comp ADX 2 Mandatory
input ENUM_TIMEFRAMES Comp_ADX_Timeframe_2 = PERIOD_H4;//Compare ADX Timeframe 2
input int  Comp_ADX_Period_2 = 14;//Compare ADX Period 2
input double  Comp_ADX_Minimum_Level_2 = 20;//Compare ADX Minimum Level 2
input double  Comp_ADX_Maximum_Level_2 = 50;//Compare ADX Maximum Level 2
int Hndl_Comp_ADX_2;
double Comp_ADX_2[];

input bool Comp_Use_ADX_MA_Smoothing_2 = true;//Compare Use ADX MA Smoothing
input ENUM_MA_METHOD Comp_ADX_MA_Type_2 = MODE_EMA;//Compare ADX MA Type
input int Comp_ADX_MA_Period_2 = 7;//Compare ADX MA Period
int Comp_Hndl_MA_ADX_2;
double Comp_MA_ADX_2[];



//--//



input group "Trade Restriction Settings"
input string S_1 = "________________________ Daily ATR % Restriction ___________________________";//Daily ATR % Restriction
input bool Use_ATR_Daily_Restriction =  true;//ATR% Daily Restriction
input double ATR_Daily_Restriction_Multiplier = 1.5;//ATR% Daily Multiplier For Restriction
input ENUM_TIMEFRAMES ATR_Daily_Restriction_TimeFrame = PERIOD_D1;//ATR% Daily Restriction TimeFrame
input int ATR_Daily_Restriction_Period =  14;
int Hndl_Daily_ATR_Rest;
double ATR_Daily_Rest[];

input string S_22222 = "________________________TRADE RESTRICTION MODULE – \"Extreme Price Range Blocker___________________________";//TRADE RESTRICTION MODULE – \"Extreme Price Range Blocker
input bool Use_ExtremeRange_Restriction = true;  
input ENUM_TIMEFRAMES ExtremeRange_TF  = PERIOD_H4;
input int ExtremeRange_Candle_Count  = 20;
input double ExtremeRange_Buffer_Percent  = 0.1;
input bool Journal_ExtremeRange_Block = true;

input string S_2 = "________________________ RSI Restriction ___________________________";//RSI Restriction
input bool RSI_OverBought_Filter = true;
input double RSI_Buy_Threshold = 70;
input double RSI_Sell_Threshold = 30;
input int No_Of_Candles_To_Reset_RSI = 5;
input ENUM_TIMEFRAMES RSI_Res_TF = PERIOD_CURRENT; // RSI TF (TradeRestriction)
input int RSI_Period_Res = 14; // RSI Period (TradeRestriction)
input ENUM_APPLIED_PRICE RSI_Res_AppliedPrice = PRICE_CLOSE; // RSI Applied Price (TradeRestriction)

input string S_22 = "________________________ Streak Trigger - No Trade Untill Reset ___________________________";//Streak Trigger - No Trade Untill Reset
input bool Enable_Streak_Trigger = true;//Enable Streak Trigger
input int Max_Consecutive_SL_Streak = 3;//Max Consecutive SL Streak
input int Max_Consecutive_TP_Streak = 3;//Max Consecutive TP Streak
input ENUM_TIMEFRAMES Reset_TF = PERIOD_D1;//Reset TimeFrame

input string S_222 = "________________________ Max Spread Before Entry ___________________________";//Max Spread Before Entry
input bool Enable_Spread_Protection = true;//Enable Spread Protection
input int Max_Spread_Pips = 10;//Max Spread Pips
input bool Log_Spred_Blocks = true;












//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
input group "Time Management Settings (ServerTimezone)"
input bool use_time_filter_signals = false; //Filter Signal Counting Time
input int signal_time_start_hour = 16; //Signal Counting Time Start Hour
input int signal_time_start_minute = 30; //Signal Counting Time Start Minute
input int signal_time_end_hour = 23; //Signal Counting Time End Hour
input int signal_time_end_minute = 0; //Signal Counting Time End Minute
input bool use_time_filter_notrades = false; //Use No New Trades Filter
input int notrades_time_start_hour = 20; //No New Trades Start Hour
input int notrades_time_start_minute = 00; //No New Trades Start Minute
input int notrades_time_end_hour = 23; //No New Trades End Hour
input int notrades_time_end_minute = 59; //No New Trades End Minute
input bool use_time_filter_noprocessing = false; //Use No Trades Processing Filter
input int noprocessing_time_start_hour = 20; //No Trades Processing Start Hour
input int noprocessing_time_start_minute = 0; //No Trades Processing Start Minute
input int noprocessing_time_end_hour = 23; //No Trades Processing End Hour
input int noprocessing_time_end_minute = 59; //No Trades Processing End Minute
input bool use_friday_closing = false; //Use Friday Closing Time
input int fridayclosing_time_start_hour = 20; //Friday Closing Time Hour
input int fridayclosing_time_start_minute = 0; //Friday Closing Time Minute

input bool use_everyday_closing = false; //Use Everyday Closing Time
input int everydayclosing_time_start_hour = 20; //Everyday Closing Time Hour
input int everydayclosing_time_start_minute = 0; //Everyday Closing Time Minute
input bool trade_mon = true; // Trade Monday
input bool trade_tue = true; // Trade Tuesday
input bool trade_wed = true; // Trade Wednesday
input bool trade_thu = true; // Trade Thursday
input bool trade_fri = true; // Trade Friday
input bool trade_sat = true; // Trade Saturday
input bool trade_sun = true; // Trade Sunday
input bool use_week_reset = false; //Use Weekly Reset
input ENUM_DAY_OF_WEEK wreset_day = WEDNESDAY; // Weekly Reset Day
input int wreset_start_hour = 20; //Weekly Reset Time Hour
input int wreset_start_minute = 0; //Weekly Reset Time Minute

input bool No_More_Trade_On_Friday = true;
input int Friday_No_New_Trade_Start_Hour = 15;
input int Friday_No_New_Trade_Start_Minute = 0;


input bool Enable_Monday_Trading_Filter = true;
input string Monday_Trading_Start_Hour = "02:00";









input group "----------------Filter News forexfactory.com-----------------"
string file_name = "News_File_12.csv";
input string seppp              =  "______________________ News Settings_________________________"; //News----------
input bool Enable_Red_News_Filter = true;//Enable Red News Filter
input int Block_Trade_Minutes_Before_ = 20;//Block Trade Minutes Before
int Block_Trade_Minutes_Before = Block_Trade_Minutes_Before_*60; 
input int Block_Trade_Minutes_After_ = 30;//Block Trade Minutes After
int Block_Trade_Minutes_After = Block_Trade_Minutes_After_*60;

input bool Enable_Special_Event_Close = true;//Enable Special Event Close
input string Special_Events_FOMC_KeyWords = "FOMC,FOMC";//Special Events FOMC KeyWords(Separated By ",")
input int Close_Trades_Minutes_Before_FOMC_ = 60;//Close Trades Minutes Before FOMC
int Close_Trades_Minutes_Before_FOMC =  Close_Trades_Minutes_Before_FOMC_*60;
input bool Block_New_Trades_Until_End_Of_Day_FOMC = true;//Block New Trades Until End Of Day FOMC
input string Special_Events_NFP_KeyWords = "NFP,NFP";//Special Events NFP KeyWords(Separated By ",")
input int Close_Trades_Minutes_Before_NFP_ = 45;//Close Trades Minutes Before NFP
int Close_Trades_Minutes_Before_NFP = Close_Trades_Minutes_Before_NFP_*60;
input bool Block_New_Trades_Until_End_Of_Day_NFP = true;//Block New Trades Until End Of Day NFP






bool                         UseNewsFilter                       = true; //Use news filter
bool                         News_Close_Active = false;  // Close All
input bool                         Display_News                        = true;
int                          Min_Before_News_                 = 15;//Halt trade before news in Mins
int                          Min_After_News_                 = 15;//Continue trade after news in Mins
int Min_Before_News = Min_Before_News_*60;
int Min_After_News = Min_After_News_*60;
input string sep4_1             =  "____________________ News Currency Filter (Standard+Special)___________________"; //News----------
input string                       News_Symbols                        = "AUD,CAD,CHF,CNY,EUR,GBP,JPY,NZD,USD";//
input string sep4_2             =  "_____________________ News Impact Filter (Standard+Special)____________________"; //News----------
input bool                         High_Impact                         = true;//High Impact
input bool                         Medium_Impact                       = true;//Medium Impact
input bool                         Low_Impact                          = true;//Low Impact
input string sep4_3             =  "__________________ News KeyWords Filter For Standard Only_____________________"; //News----------
input bool                         Use_Allow_KeyWords                  = false;
input string                       Allowed_KeyWords                    = "CPI,GDP,Interest Rates";
input bool                         Use_DoNot_Allow_KeyWords            = false;
input string                       DoNot_Allowed_KeyWords              = "Speaks,Speeches";
string                              sep                                 = ",";
ushort                              u_sep                               = StringGetCharacter(sep,0);
bool is_news = true;










bool vtrade_mon = true;
bool vtrade_tue = true;
bool vtrade_wed = true;
bool vtrade_thu = true;
bool vtrade_fri = true;
bool vtrade_sat = true;
bool vtrade_sun = true;


int ma1_h, ma2_h, ma3_h, ma5_h, ma4_h, exec_psar_h, exec_adx_h, exec_st_h, exec_rsi_h, conf_psar_h, conf_adx_h, conf_st_h, conf_rsi_h;
double ma1[], ma2[], ma3[],ma4[],ma5[], psar[], adx[], st[], rsi[], conf_psar[], conf_adx[], conf_st[], conf_rsi[];

int comp_ma_h, comp_st_h, comp_rsi_h_1,comp_rsi_h_2;
double comp_ma[], comp_st[],comp_rsi_1[],comp_rsi_2[];


int atrpct_h;
double atrpct[];

int st1_h, st2_h, st3_h;
double st1[], st2[], st3[];


double Ask, Bid;
int buy_limits, sell_limits, buy_stops, sell_stops, buys, sells;

int streak_buys, streak_sells;
double range_high, range_low;

int RSI_Partial_Handle;
int RSI_Partial_Handle_HDST;
int RSI_Partial_Handle_SDST;
double RSI_P[];

int RSI_Res_Handle;
double RSI_Res[];

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkBuyThresRSI()
  {
   if(!RSI_OverBought_Filter)
     {
      return true;
     }

   for(int i = 1; i < No_Of_Candles_To_Reset_RSI;i++)
     {
      if(RSI_Res[i] > RSI_Buy_Threshold)
        {
         Print("Trade cannot open because of RSI Threshold");
         return false;
        }
     }
   return true;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkSellThresRSI()
  {
   if(!RSI_OverBought_Filter)
     {
      return true;
     }

   for(int i = 1; i < No_Of_Candles_To_Reset_RSI;i++)
     {
      if(RSI_Res[i] < RSI_Sell_Threshold)
        {
         Print("Trade cannot open because of RSI Threshold");
         return false;
        }
     }
   return true;
  }



int Magic_1 = 0;
int Magic_2 = 0;
int Magic_3 = 0;




int Magic_Addon = 0;










//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

string Status_Txt(string s , bool main_flg , bool mand_flg)
{

      if(main_flg)
      {
       s = s+" Enabled ";
       if(mand_flg)
       {
        s = s+"Mandatory ";
       }
       else
       {
        s = s+"Optional ";
       }
      }
      else
      {
       s = s+" Disabled ";
      }
  return s+"➤"; 
}



//=== COC Dashboard Global Variables ===
datetime last_coc_status_update = 0;
datetime last_coc_command_check = 0;
bool coc_ea_initialized = false;
bool coc_override = false;
bool coc_is_paused = false;
string coc_instance_uuid = "";  // Unique identifier for this EA instance
bool coc_remote_control_active = false;

// COC Performance tracking
double coc_total_profit = 0.0;
int coc_total_trades = 0;
double coc_max_drawdown = 0.0;
double coc_peak_equity = 0.0;
double coc_current_equity = 0.0;

// COC Remote control variables
double coc_remote_risk_percent = 1.0;
double coc_remote_lot_size = 0.01;
bool coc_remote_use_fixed_lot = false;
int coc_remote_max_positions = 3;
bool coc_remote_trading_enabled = true;

// COC Dashboard display
string dashboard_prefix = "DASH_";

//+------------------------------------------------------------------+
//| COC Dashboard Integration Functions                               |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Generate Instance UUID                                           |
//+------------------------------------------------------------------+
string COC_GenerateInstanceUUID()
{
    // Generate pseudo-UUID using account info, symbol, magic number, and timestamp
    long account = AccountInfoInteger(ACCOUNT_LOGIN);
    long timestamp = TimeCurrent();
    int random_val = MathRand();
    
    string uuid = IntegerToString(eamagic) + "-" + 
                  IntegerToString(account) + "-" + 
                  Symbol() + "-" + 
                  IntegerToString(timestamp) + "-" + 
                  IntegerToString(random_val);
    
    return uuid;
}

//+------------------------------------------------------------------+
//| Register EA with COC Backend                                     |
//+------------------------------------------------------------------+
bool COC_RegisterEAWithBackend()
{
    if(!Enable_COC_Dashboard) return false;
    
    string url = COC_Backend_URL + "/api/ea/register";
    string headers = "Content-Type: application/json\r\n";
    
    // Get current account info
    double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double account_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    string account_currency = AccountInfoString(ACCOUNT_CURRENCY);
    long account_leverage = AccountInfoInteger(ACCOUNT_LEVERAGE);
    
    string json = "{";
    json += "\"uuid\":\"" + coc_instance_uuid + "\",";
    json += "\"magic_number\":" + IntegerToString(eamagic) + ",";
    json += "\"strategy_tag\":\"" + COC_Strategy_Tag + "\",";
    json += "\"symbol\":\"" + Symbol() + "\",";
    json += "\"timeframe\":\"" + EnumToString(Period()) + "\",";
    json += "\"ea_name\":\"" + EA_Name + "\",";
    json += "\"account_balance\":" + DoubleToString(account_balance, 2) + ",";
    json += "\"account_equity\":" + DoubleToString(account_equity, 2) + ",";
    json += "\"account_currency\":\"" + account_currency + "\",";
    json += "\"account_leverage\":" + IntegerToString(account_leverage) + ",";
    json += "\"status\":\"ACTIVE\",";
    json += "\"last_update\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
    json += "}";
    
    // Send HTTP request
    char post_data[];
    char result[];
    string result_headers;
    
    StringToCharArray(json, post_data, 0, StringLen(json));
    
    int timeout = 5000; // 5 seconds timeout
    int response_code = WebRequest("POST", url, headers, timeout, post_data, result, result_headers);
    
    if(response_code == 200 || response_code == 201)
    {
        Print("✅ COC Dashboard: EA registered successfully");
        return true;
    }
    else
    {
        Print("❌ COC Dashboard: Registration failed with code: ", response_code);
        return false;
    }
}

//+------------------------------------------------------------------+
//| Send Status Update to COC Backend                               |
//+------------------------------------------------------------------+
void COC_SendStatusUpdate()
{
    if(!Enable_COC_Dashboard || !coc_ea_initialized) return;
    
    // Check if enough time has passed since last update
    if(TimeCurrent() - last_coc_status_update < COC_Status_Update_Interval) return;
    
    string url = COC_Backend_URL + "/api/ea/status/" + coc_instance_uuid;
    string headers = "Content-Type: application/json\r\n";
    
    // Calculate current statistics
    double current_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    coc_current_equity = current_equity;
    
    // Update peak equity and drawdown
    if(current_equity > coc_peak_equity)
        coc_peak_equity = current_equity;
    
    double current_drawdown = (coc_peak_equity > 0) ? ((coc_peak_equity - current_equity) / coc_peak_equity) * 100 : 0;
    if(current_drawdown > coc_max_drawdown)
        coc_max_drawdown = current_drawdown;
    
    // Count current positions
    int buy_positions = Tot_Trades(OP_BUY);
    int sell_positions = Tot_Trades(OP_SELL);
    int total_positions = buy_positions + sell_positions;
    
    // Calculate total profit from all positions
    double total_profit_current = 0.0;
    for(int i = 0; i < PositionsTotal(); i++)
    {
        if(PositionSelectByIndex(i) && PositionGetInteger(POSITION_MAGIC) == eamagic)
        {
            total_profit_current += PositionGetDouble(POSITION_PROFIT);
        }
    }
    
    string json = "{";
    json += "\"status\":\"" + (coc_is_paused ? "PAUSED" : "ACTIVE") + "\",";
    json += "\"account_balance\":" + DoubleToString(current_balance, 2) + ",";
    json += "\"account_equity\":" + DoubleToString(current_equity, 2) + ",";
    json += "\"current_profit\":" + DoubleToString(total_profit_current, 2) + ",";
    json += "\"total_profit\":" + DoubleToString(coc_total_profit, 2) + ",";
    json += "\"max_drawdown\":" + DoubleToString(coc_max_drawdown, 2) + ",";
    json += "\"total_trades\":" + IntegerToString(coc_total_trades) + ",";
    json += "\"open_positions\":" + IntegerToString(total_positions) + ",";
    json += "\"buy_positions\":" + IntegerToString(buy_positions) + ",";
    json += "\"sell_positions\":" + IntegerToString(sell_positions) + ",";
    json += "\"remote_control\":" + (coc_remote_control_active ? "true" : "false") + ",";
    json += "\"last_update\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
    json += "}";
    
    // Send HTTP request
    char post_data[];
    char result[];
    string result_headers;
    
    StringToCharArray(json, post_data, 0, StringLen(json));
    
    int timeout = 5000;
    int response_code = WebRequest("PUT", url, headers, timeout, post_data, result, result_headers);
    
    if(response_code == 200)
    {
        last_coc_status_update = TimeCurrent();
    }
    else
    {
        Print("⚠️ COC Dashboard: Status update failed with code: ", response_code);
    }
}

//+------------------------------------------------------------------+
//| Check for Commands from COC Backend                             |
//+------------------------------------------------------------------+
void COC_CheckForCommands()
{
    if(!Enable_COC_Dashboard || !coc_ea_initialized || !COC_Enable_Remote_Control) return;
    
    // Check if enough time has passed since last command check
    if(TimeCurrent() - last_coc_command_check < COC_Command_Check_Interval) return;
    
    string url = COC_Backend_URL + "/api/ea/commands/" + coc_instance_uuid;
    
    // Send HTTP GET request
    char result[];
    string result_headers;
    
    int timeout = 5000;
    int response_code = WebRequest("GET", url, "", timeout, result, result_headers);
    
    if(response_code == 200)
    {
        string response = CharArrayToString(result);
        COC_ProcessCommands(response);
        last_coc_command_check = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Process Commands from COC Backend                               |
//+------------------------------------------------------------------+
void COC_ProcessCommands(string json_response)
{
    // Simple JSON parsing for commands
    if(StringFind(json_response, "\"command\":\"PAUSE\"") >= 0)
    {
        coc_is_paused = true;
        coc_remote_control_active = true;
        Print("🛑 COC Dashboard: EA PAUSED by remote command");
    }
    else if(StringFind(json_response, "\"command\":\"RESUME\"") >= 0)
    {
        coc_is_paused = false;
        coc_remote_control_active = true;
        Print("▶️ COC Dashboard: EA RESUMED by remote command");
    }
    else if(StringFind(json_response, "\"command\":\"CLOSE_ALL\"") >= 0)
    {
        COC_CloseAllPositions();
        Print("❌ COC Dashboard: All positions closed by remote command");
    }
    else if(StringFind(json_response, "\"command\":\"DISABLE_TRADING\"") >= 0)
    {
        coc_remote_trading_enabled = false;
        coc_remote_control_active = true;
        Print("🚫 COC Dashboard: Trading disabled by remote command");
    }
    else if(StringFind(json_response, "\"command\":\"ENABLE_TRADING\"") >= 0)
    {
        coc_remote_trading_enabled = true;
        coc_remote_control_active = true;
        Print("✅ COC Dashboard: Trading enabled by remote command");
    }
    
    // Parse parameter updates
    COC_ParseParameterUpdates(json_response);
}

//+------------------------------------------------------------------+
//| Parse Parameter Updates from Commands                           |
//+------------------------------------------------------------------+
void COC_ParseParameterUpdates(string json_response)
{
    // Simple parameter parsing - can be enhanced with proper JSON parser
    int risk_pos = StringFind(json_response, "\"risk_percent\":");
    if(risk_pos >= 0)
    {
        int start = StringFind(json_response, ":", risk_pos) + 1;
        int end = StringFind(json_response, ",", start);
        if(end == -1) end = StringFind(json_response, "}", start);
        
        string risk_str = StringSubstr(json_response, start, end - start);
        StringReplace(risk_str, " ", "");
        StringReplace(risk_str, "\"", "");
        
        double new_risk = StringToDouble(risk_str);
        if(new_risk > 0 && new_risk <= 10) // Safety limits
        {
            coc_remote_risk_percent = new_risk;
            Print("📊 COC Dashboard: Risk percent updated to ", new_risk, "%");
        }
    }
    
    int lot_pos = StringFind(json_response, "\"lot_size\":");
    if(lot_pos >= 0)
    {
        int start = StringFind(json_response, ":", lot_pos) + 1;
        int end = StringFind(json_response, ",", start);
        if(end == -1) end = StringFind(json_response, "}", start);
        
        string lot_str = StringSubstr(json_response, start, end - start);
        StringReplace(lot_str, " ", "");
        StringReplace(lot_str, "\"", "");
        
        double new_lot = StringToDouble(lot_str);
        if(new_lot > 0 && new_lot <= 100) // Safety limits
        {
            coc_remote_lot_size = new_lot;
            Print("💰 COC Dashboard: Lot size updated to ", new_lot);
        }
    }
}

//+------------------------------------------------------------------+
//| Close All Positions                                             |
//+------------------------------------------------------------------+
void COC_CloseAllPositions()
{
    for(int i = PositionsTotal() - 1; i >= 0; i--)
    {
        if(PositionSelectByIndex(i) && PositionGetInteger(POSITION_MAGIC) == eamagic)
        {
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            Trade.PositionClose(ticket);
        }
    }
}

//+------------------------------------------------------------------+
//| Export Data to JSON File                                        |
//+------------------------------------------------------------------+
void COC_ExportDataToJSON()
{
    if(!COC_Auto_Export_Data) return;
    
    string filename = COC_Data_Path + "ea_" + IntegerToString(eamagic) + ".json";
    
    // Calculate current statistics
    double current_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    double current_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    int buy_positions = Tot_Trades(OP_BUY);
    int sell_positions = Tot_Trades(OP_SELL);
    
    string json = "{\n";
    json += "  \"ea_info\": {\n";
    json += "    \"uuid\": \"" + coc_instance_uuid + "\",\n";
    json += "    \"name\": \"" + EA_Name + "\",\n";
    json += "    \"magic_number\": " + IntegerToString(eamagic) + ",\n";
    json += "    \"strategy_tag\": \"" + COC_Strategy_Tag + "\",\n";
    json += "    \"symbol\": \"" + Symbol() + "\",\n";
    json += "    \"timeframe\": \"" + EnumToString(Period()) + "\"\n";
    json += "  },\n";
    json += "  \"account_info\": {\n";
    json += "    \"balance\": " + DoubleToString(current_balance, 2) + ",\n";
    json += "    \"equity\": " + DoubleToString(current_equity, 2) + ",\n";
    json += "    \"currency\": \"" + AccountInfoString(ACCOUNT_CURRENCY) + "\",\n";
    json += "    \"leverage\": " + IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)) + "\n";
    json += "  },\n";
    json += "  \"trading_status\": {\n";
    json += "    \"status\": \"" + (coc_is_paused ? "PAUSED" : "ACTIVE") + "\",\n";
    json += "    \"trading_enabled\": " + (coc_remote_trading_enabled ? "true" : "false") + ",\n";
    json += "    \"remote_control\": " + (coc_remote_control_active ? "true" : "false") + ",\n";
    json += "    \"open_positions\": " + IntegerToString(buy_positions + sell_positions) + ",\n";
    json += "    \"buy_positions\": " + IntegerToString(buy_positions) + ",\n";
    json += "    \"sell_positions\": " + IntegerToString(sell_positions) + "\n";
    json += "  },\n";
    json += "  \"performance\": {\n";
    json += "    \"total_profit\": " + DoubleToString(coc_total_profit, 2) + ",\n";
    json += "    \"max_drawdown\": " + DoubleToString(coc_max_drawdown, 2) + ",\n";
    json += "    \"total_trades\": " + IntegerToString(coc_total_trades) + ",\n";
    json += "    \"peak_equity\": " + DoubleToString(coc_peak_equity, 2) + "\n";
    json += "  },\n";
    json += "  \"last_update\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"\n";
    json += "}";
    
    // Save to file
    int file_handle = FileOpen(filename, FILE_WRITE|FILE_TXT);
    if(file_handle != INVALID_HANDLE)
    {
        FileWriteString(file_handle, json);
        FileClose(file_handle);
    }
}

//+------------------------------------------------------------------+
//| Track Trade for COC Dashboard                                   |
//+------------------------------------------------------------------+
void COC_TrackTrade(double profit_loss)
{
    if(!Enable_COC_Dashboard) return;
    
    // Update total trades and profit
    coc_total_trades++;
    coc_total_profit += profit_loss;
    
    // Send immediate update for trade closure
    if(profit_loss != 0) // Only for closed trades
    {
        COC_SendStatusUpdate();
        COC_ExportDataToJSON();
    }
}

//+------------------------------------------------------------------+
//| Enhanced Lot Size Calculation with COC Remote Control          |
//+------------------------------------------------------------------+
double COC_GetLotSize(double risk_amount)
{
    if(Enable_COC_Dashboard && coc_remote_control_active)
    {
        if(coc_remote_use_fixed_lot)
            return coc_remote_lot_size;
        else
        {
            // Use remote risk percentage
            double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
            double risk_money = account_balance * (coc_remote_risk_percent / 100.0);
            
            // Calculate lot size based on risk
            double pip_value = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
            if(pip_value > 0)
                return NormalizeDouble(risk_money / (Default_Stop_Loss * pip_value), 2);
        }
    }
    
    // Fall back to original lot calculation
    if(use_dynamic_lots)
    {
        double account_balance = AccountInfoDouble(ACCOUNT_BALANCE);
        double risk_money = MathMin(risk_amount, account_balance * 0.02); // Max 2% risk
        double pip_value = SymbolInfoDouble(Symbol(), SYMBOL_TRADE_TICK_VALUE);
        if(pip_value > 0)
            return NormalizeDouble(risk_money / (Default_Stop_Loss * pip_value), 2);
    }
    
    return fixlot;
}

void Create_DashBaord()
{
    if(Show_Dashboard)
   {
      RectLabelCreate();
      LabelCreate(dashboard_prefix+"Lab0",100,20,"EA: "+EA_Name+" 🎛️ COC Enhanced",12,C'236,233,216',"Segoe UI Bold"); 
      LabelCreate(dashboard_prefix+"Lab1",20,50,"【Magic Number】:"+eamagic,10,C'236,233,216',"Segoe UI Bold");   
      LabelCreate(dashboard_prefix+"Lab2",20,70,"【Symbol】: "+_Symbol,10,C'236,233,216',"Segoe UI Bold"); 
      
      // COC Dashboard Status
      if(Enable_COC_Dashboard)
      {
          string coc_status = coc_ea_initialized ? "✅ Connected" : "❌ Disconnected";
          string remote_status = coc_remote_control_active ? "🎛️ Remote" : "📱 Local";
          string trading_status = coc_is_paused ? "⏸️ Paused" : (coc_remote_trading_enabled ? "▶️ Active" : "🛑 Disabled");
          
          LabelCreate(dashboard_prefix+"COC_Lab1",20,90,"【COC Status】: "+coc_status,10,C'236,233,216',"Segoe UI Bold");
          LabelCreate(dashboard_prefix+"COC_Lab2",20,110,"【Control Mode】: "+remote_status,10,C'236,233,216',"Segoe UI Bold");
          LabelCreate(dashboard_prefix+"COC_Lab3",20,130,"【Trading Status】: "+trading_status,10,C'236,233,216',"Segoe UI Bold");
          LabelCreate(dashboard_prefix+"COC_Lab4",20,150,"【UUID】: "+StringSubstr(coc_instance_uuid,0,20)+"...",9,C'180,180,180',"Segoe UI");
          
          LabelCreate(dashboard_prefix+"Lab3",20,170,"【Active Trades Sell】: "+Tot_Trades(OP_SELL),10,C'236,233,216',"Segoe UI Bold"); 
          LabelCreate(dashboard_prefix+"Lab4",20,190,"【Active Trades Buy】: "+Tot_Trades(OP_BUY),10,C'236,233,216',"Segoe UI Bold");
      }
      else
      {
          LabelCreate(dashboard_prefix+"Lab3",20,90,"【Active Trades Sell】: "+Tot_Trades(OP_SELL),10,C'236,233,216',"Segoe UI Bold"); 
          LabelCreate(dashboard_prefix+"Lab4",20,110,"【Active Trades Buy】: "+Tot_Trades(OP_BUY),10,C'236,233,216',"Segoe UI Bold");
      }
      int y_offset = Enable_COC_Dashboard ? 80 : 0; // Adjust positions if COC is enabled
      
      LabelCreate(dashboard_prefix+"Lab5",20,130+y_offset,"【SL Logic】:",10,C'236,233,216',"Segoe UI Bold");
      LabelCreate(dashboard_prefix+"Lab6",20,150+y_offset,"【Trailing Logic】:",10,C'236,233,216',"Segoe UI Bold");
      LabelCreate(dashboard_prefix+"Lab7",20,170+y_offset,"【Breakeven】:",10,C'236,233,216',"Segoe UI Bold");
      
   
      if(Enable_Confluence_Master)
      {
       LabelCreate(dashboard_prefix+"Lab8",20,190+y_offset,"【Confluence】:"+(Enable_Confluence_Master?"Enabled":"Disabled"),10,C'236,233,216',"Segoe UI Bold");
       LabelCreate(dashboard_prefix+"Lab9",20,210+y_offset,Status_Txt("RSI1",Regime1_Use_RSI_Confluence_1,Regime1_RSI_Confluence_1_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab10",20,230+y_offset,Status_Txt("RSI2",Regime1_Use_RSI_Confluence_2,Regime1_RSI_Confluence_2_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab11",20,250+y_offset,Status_Txt("ADX1",Regime1_Use_ADX_Confluence_1,Regime1_ADX_Confluence_1_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab12",20,270+y_offset,Status_Txt("ADX2",Regime1_Use_ADX_Confluence_2,Regime1_ADX_Confluence_2_Mandatory),10,C'236,233,216',"Segoe UI");
      }
      else
      {
       LabelCreate(dashboard_prefix+"Lab8",20,190+y_offset,"【Confluence】:"+"Disabled",10,C'236,233,216',"Segoe UI Bold");
       LabelCreate(dashboard_prefix+"Lab9",20,210+y_offset,"RSI1"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab10",20,230+y_offset,"RSI2"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab11",20,250+y_offset,"ADX1"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab12",20,270+y_offset,"ADX2"+"Disabled",10,C'236,233,216',"Segoe UI"); 
      }

      if(Enable_Comparison_Master)
      {
       LabelCreate(dashboard_prefix+"Lab13",20,290+y_offset,"【Strength】:"+"Enabled",10,C'236,233,216',"Segoe UI Bold");
       LabelCreate(dashboard_prefix+"Lab14",20,310+y_offset,Status_Txt("MA",Check_comp_ma,comp_ma_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab15",20,330+y_offset,Status_Txt("ST",Check_comp_st,comp_st_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab16",20,350+y_offset,Status_Txt("RSI1",Check_comp_rsi_1,comp_rsi_1_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab17",20,370+y_offset,Status_Txt("RSI2",Check_comp_rsi_2,comp_rsi_2_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab18",20,390+y_offset,Status_Txt("ADX1",Comp_Use_ADX_1,Comp_adx_1_Mandatory),10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab19",20,410+y_offset,Status_Txt("ADX2",Comp_Use_ADX_2,Comp_adx_2_Mandatory),10,C'236,233,216',"Segoe UI");
      }
      else
      {
       LabelCreate(dashboard_prefix+"Lab13",20,290+y_offset,"【Strength】:"+"Disabled",10,C'236,233,216',"Segoe UI Bold");
       LabelCreate(dashboard_prefix+"Lab14",20,310+y_offset,"MA"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab15",20,330+y_offset,"ST"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab16",20,350+y_offset,"RSI1"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab17",20,370+y_offset,"RSI2"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab18",20,390+y_offset,"ADX1"+"Disabled",10,C'236,233,216',"Segoe UI");
       LabelCreate(dashboard_prefix+"Lab19",20,410+y_offset,"ADX2"+"Disabled",10,C'236,233,216',"Segoe UI");       
      }
      
      
      
      if(Use_Primary_ATR)
      {
       LabelCreate(dashboard_prefix+"Lab20",20,430+y_offset,"【Voltality】"+"Enabled",10,C'236,233,216',"Segoe UI Bold");
      }
      else
      {
       LabelCreate(dashboard_prefix+"Lab20",20,430+y_offset,"【Voltality】"+"Disabled",10,C'236,233,216',"Segoe UI Bold");
      }
      

   }
}

void Update_DashBoards()
{
 if(!Show_Dashboard) return;

 // Update COC Dashboard Status
 if(Enable_COC_Dashboard)
 {
     string coc_status = coc_ea_initialized ? "✅ Connected" : "❌ Disconnected";
     string remote_status = coc_remote_control_active ? "🎛️ Remote" : "📱 Local";
     string trading_status = coc_is_paused ? "⏸️ Paused" : (coc_remote_trading_enabled ? "▶️ Active" : "🛑 Disabled");
     
     ObjectSetString(0,dashboard_prefix+"COC_Lab1",OBJPROP_TEXT,"【COC Status】: "+coc_status);
     ObjectSetString(0,dashboard_prefix+"COC_Lab2",OBJPROP_TEXT,"【Control Mode】: "+remote_status);
     ObjectSetString(0,dashboard_prefix+"COC_Lab3",OBJPROP_TEXT,"【Trading Status】: "+trading_status);
     
     // Update performance info
     string perf_info = "💰 P&L: $" + DoubleToString(coc_total_profit, 2) + " | 📉 DD: " + DoubleToString(coc_max_drawdown, 1) + "%";
     if(ObjectFind(0, dashboard_prefix+"COC_Lab5") < 0)
         LabelCreate(dashboard_prefix+"COC_Lab5",400,90,perf_info,9,C'180,180,180',"Segoe UI");
     else
         ObjectSetString(0,dashboard_prefix+"COC_Lab5",OBJPROP_TEXT,perf_info);
 }

 ObjectSetString(0,dashboard_prefix+"Lab3",OBJPROP_TEXT,"【Active Trades Sell】: "+Tot_Trades(OP_SELL));
 ObjectSetString(0,dashboard_prefix+"Lab4",OBJPROP_TEXT,"【Active Trades Buy】: "+Tot_Trades(OP_BUY));
 
 if(Enable_Confluence_Master)
 {
  if(Regime1_Use_RSI_Confluence_1)
  {
   //Print("Enter ");
   CopyBuffer(Hndl_Regime1_RSI_1,0,0,10,Regime1_RSI_1);
   bool status = !(Regime1_RSI_1[1]<Regime1_RSI_Minimum_Level_1 || Regime1_RSI_1[1]>Regime1_RSI_Maximum_Level_1);
   LabelCreate(dashboard_prefix+"Lab9_9",230,210,DoubleToString(Regime1_RSI_1[1],2)+" | Band: "+DoubleToString(Regime1_RSI_Minimum_Level_1,2)+"-"+DoubleToString(Regime1_RSI_Maximum_Level_1,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
  }
  if(Regime1_Use_RSI_Confluence_2)
  {
   //Print("Enter ");
   CopyBuffer(Hndl_Regime1_RSI_2,0,0,10,Regime1_RSI_2);
   bool status = !(Regime1_RSI_2[1]<Regime1_RSI_Minimum_Level_2 || Regime1_RSI_2[1]>Regime1_RSI_Maximum_Level_2);
   LabelCreate(dashboard_prefix+"Lab10_10",230,230,DoubleToString(Regime1_RSI_2[1],2)+" | Band: "+DoubleToString(Regime1_RSI_Minimum_Level_2,2)+"-"+DoubleToString(Regime1_RSI_Maximum_Level_2,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
  
  }  
   if(Regime1_Use_ADX_Confluence_1)
     {
      bool status = false;
      double val = 0;     
      if(Regime1_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Regime1_Hndl_MA_ADX_1,0,0,10,Regime1_MA_ADX_1);
         val = Regime1_MA_ADX_1[1];
         if(!(Regime1_MA_ADX_1[1]<Regime1_ADX_Minimum_Level_1 || Regime1_MA_ADX_1[1]>Regime1_ADX_Maximum_Level_1))
           {
              status = true;                            
           }
        }
      else
        {
         CopyBuffer(Hndl_Regime1_ADX_1,0,0,10,Regime1_ADX_1);
         val = Regime1_ADX_1[1];
         if(!(Regime1_ADX_1[1]<Regime1_ADX_Minimum_Level_1 || Regime1_ADX_1[1]>Regime1_ADX_Maximum_Level_1))
           {
             status = true;                         
           }
        }
        LabelCreate(dashboard_prefix+"Lab11_11",240,250,DoubleToString(val,2)+" | Band: "+DoubleToString(Regime1_ADX_Minimum_Level_1,2)+"-"+DoubleToString(Regime1_ADX_Maximum_Level_1,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
     }
   if(Regime1_Use_ADX_Confluence_2)
     {
      bool status = false;
      double val = 0;     
      if(Regime1_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Regime1_Hndl_MA_ADX_2,0,0,10,Regime1_MA_ADX_2);
         val = Regime1_MA_ADX_2[1];
         if(!(Regime1_MA_ADX_2[1]<Regime1_ADX_Minimum_Level_2 || Regime1_MA_ADX_2[1]>Regime1_ADX_Maximum_Level_2))
           {
              status = true;                            
           }
        }
      else
        {
         CopyBuffer(Hndl_Regime1_ADX_2,0,0,10,Regime1_ADX_2);
         val = Regime1_ADX_2[1];
         if(!(Regime1_ADX_2[1]<Regime1_ADX_Minimum_Level_2 || Regime1_ADX_2[1]>Regime1_ADX_Maximum_Level_2))
           {
             status = true;                         
           }
        }
        LabelCreate(dashboard_prefix+"Lab12_12",240,270,DoubleToString(val,2)+" | Band: "+DoubleToString(Regime1_ADX_Minimum_Level_2,2)+"-"+DoubleToString(Regime1_ADX_Maximum_Level_2,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
     }
 }
 if(Enable_Comparison_Master)
 {
   if(Check_comp_ma)
   {
      CopyBuffer(comp_ma_h, 0, 0, 5, comp_ma);
      double val = comp_ma[1];
      bool buy_status = ((comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) < comp_ma[1]) ||  (!comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) > comp_ma[1]));
      bool sell_status = ((comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) > comp_ma[1]) ||  (!comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) < comp_ma[1]));
      LabelCreate(dashboard_prefix+"Lab14_14",250,310,DoubleToString(val,2)+" | Close: "+DoubleToString(iClose(comp_symbol,comp_ma_tf,1),2)+" | "+(buy_status?"Buy":"Sell"),10,C'236,233,216',"Segoe UI");
   
   }
   if(Check_comp_st)
     {
      CopyBuffer(comp_st_h, 0, 0, 5, comp_st);
      double val = comp_st[1];
      bool buy_status = ((comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) < comp_st[1]) || (!comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) > comp_st[1]));
      bool sell_status = ((comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) > comp_st[1]) || (!comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) < comp_st[1]));
      LabelCreate(dashboard_prefix+"Lab15_15",250,330,DoubleToString(val,2)+" | Close: "+DoubleToString(iClose(comp_symbol,comp_st_tf,1),2)+" | "+(buy_status?"Buy":"Sell"),10,C'236,233,216',"Segoe UI");
     }
   if(Check_comp_rsi_1)
     {
      CopyBuffer(comp_rsi_h_1, 0, 0, 5, comp_rsi_1);
      bool status = (!(comp_rsi_1[1]<RSI_Comp_Minimum_Level_1 || comp_rsi_1[1]>RSI_Comp_Maximum_Level_1)); 
      LabelCreate(dashboard_prefix+"Lab16_16",250,350,DoubleToString(comp_rsi_1[1],2)+" | Band: "+DoubleToString(RSI_Comp_Minimum_Level_1,2)+"-"+DoubleToString(RSI_Comp_Maximum_Level_1,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
     } 
   if(Check_comp_rsi_2)
     {
      CopyBuffer(comp_rsi_h_2, 0, 0, 5, comp_rsi_2);
      bool status = (!(comp_rsi_2[1]<RSI_Comp_Minimum_Level_2 || comp_rsi_2[1]>RSI_Comp_Maximum_Level_2)); 
      LabelCreate(dashboard_prefix+"Lab17_17",250,370,DoubleToString(comp_rsi_2[1],2)+" | Band: "+DoubleToString(RSI_Comp_Minimum_Level_2,2)+"-"+DoubleToString(RSI_Comp_Maximum_Level_2,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");
     }
   if(Comp_Use_ADX_1)
     {
      CopyBuffer(Hndl_Comp_ADX_1,0,0,10,Comp_ADX_1);
      double val = 0;
      bool status = false;
      if(Comp_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_1,0,0,10,Comp_MA_ADX_1);
         val = Comp_MA_ADX_1[1]; 
         status = (!(Comp_MA_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_MA_ADX_1[1]>Comp_ADX_Maximum_Level_1));
        }
      else
        {
         val = Comp_ADX_1[1]; 
         status = (!(Comp_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_ADX_1[1]>Comp_ADX_Maximum_Level_1));
        }
      LabelCreate(dashboard_prefix+"Lab18_18",250,390,DoubleToString(val,2)+" | Band: "+DoubleToString(Comp_ADX_Minimum_Level_1,2)+"-"+DoubleToString(Comp_ADX_Maximum_Level_1,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");  
     }
   if(Comp_Use_ADX_2)
     {
      CopyBuffer(Hndl_Comp_ADX_2,0,0,10,Comp_ADX_2);
      double val = 0;
      bool status = false;
      if(Comp_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_2,0,0,10,Comp_MA_ADX_2);
         val = Comp_MA_ADX_2[1]; 
         status = (!(Comp_MA_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_MA_ADX_2[1]>Comp_ADX_Maximum_Level_2));
        }
      else
        {
         val = Comp_ADX_2[1]; 
         status = (!(Comp_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_ADX_2[1]>Comp_ADX_Maximum_Level_2));
        }
      LabelCreate(dashboard_prefix+"Lab19_19",250,410,DoubleToString(val,2)+" | Band: "+DoubleToString(Comp_ADX_Minimum_Level_2,2)+"-"+DoubleToString(Comp_ADX_Maximum_Level_2,2)+" | "+(status?"✅":"❎"),10,C'236,233,216',"Segoe UI");  
     }                         
 }
      
      if(Use_Primary_ATR)
      {
       CopyBuffer(atrpct_h, 0, 0, 5, atrpct);
       bool volt_status = (NormalizeDouble(atrpct[1],2)>Minimum_ATR_Percentage && NormalizeDouble(atrpct[1],2)<Maximum_ATR_Percentage);
       LabelCreate(dashboard_prefix+"Lab21",20,450,"ATR% "+EnumToString(ATRFilterTF)+": "+DoubleToString(atrpct[1],3)+"% | Band: "+DoubleToString(Minimum_ATR_Percentage,2)+" - "+DoubleToString(Maximum_ATR_Percentage,2)+" | 🟢 "+(volt_status?"Valid":"Blocked"),10,C'236,233,216',"Segoe UI");
      }
      else
      {
      
       LabelCreate(dashboard_prefix+"Lab21",20,450,"Disabled",10,C'236,233,216',"Segoe UI");
      }  
}






int OnInit()
  {
   
   ObjectsDeleteAll(0,dashboard_prefix,-1,-1);
   
   //=== COC Dashboard Initialization ===
   if(Enable_COC_Dashboard)
   {
       Print("🚀 BOC EA with COC Dashboard Starting - Magic Number: ", eamagic);
       Print("📡 Backend URL: ", COC_Backend_URL);
       Print("🏷️ Strategy Tag: ", COC_Strategy_Tag);
       
       // Generate or use provided UUID
       if(COC_Instance_UUID == "")
           coc_instance_uuid = COC_GenerateInstanceUUID();
       else
           coc_instance_uuid = COC_Instance_UUID;
           
       Print("🆔 Instance UUID: ", coc_instance_uuid);
       
       // Initialize COC variables
       coc_peak_equity = AccountInfoDouble(ACCOUNT_EQUITY);
       coc_current_equity = coc_peak_equity;
       
       // Register with backend
       if(COC_RegisterEAWithBackend())
       {
           coc_ea_initialized = true;
           Print("✅ EA successfully registered with COC Dashboard");
       }
       else
       {
           Print("❌ Failed to register with COC Dashboard - continuing in standalone mode");
           coc_ea_initialized = false;
       }
   }

   
   
   
   /*LabelCreate(dashboard_prefix+"Lab4",20,110,"[Commander]:",10,C'236,233,216',"Segoe UI"); 
   LabelCreate(dashboard_prefix+"Lab5",20,130,"[SL Logic]:",10,C'236,233,216',"Segoe UI");
   LabelCreate(dashboard_prefix+"Lab6",20,150,"[Trailing]:",10,C'236,233,216',"Segoe UI");
   LabelCreate(dashboard_prefix+"Lab7",20,170,"[Breakeven]:",10,C'236,233,216',"Segoe UI");
   LabelCreate(dashboard_prefix+"Lab8",20,190,"[Confluence]:",10,C'236,233,216',"Segoe UI");
   LabelCreate(dashboard_prefix+"Lab9",20,210,"[Strength]:",10,C'236,233,216',"Segoe UI");
   LabelCreate(dashboard_prefix+"Lab10",20,230,"[Volatility]:",10,C'236,233,216',"Segoe UI");
   */
   
   if(Use_BB_Trailing)
     {
      Hndl_BB_Trail = iBands(_Symbol,BB_Trailing_TF,BB_Trailing_Period,0,BB_Deviation,BB_Applied_Price);
      ArraySetAsSeries(BB_Trail_UP,true);
      ArraySetAsSeries(BB_Trail_DN,true);
     }
   if(Use_RSI_Trailing)
     {
      Hndl_RSI_Trail = iRSI(_Symbol,RSI_Trailing_TF,RSI_Trailing_Period,PRICE_CLOSE);
      ArraySetAsSeries(RSI_Trail_Buffer,true);
     }


   tmee = -1;
   tm_cur = -1;
   tm_daily = -1;
   tm_st = -1;
   tm_default = -1;
   tm_d_atr_res = -1;
   tm_atr_filter = -1;

   if(Enable_Confluence_Master)
   {
      if(Regime1_Use_RSI_Confluence_1)
        {
         Hndl_Regime1_RSI_1 = iRSI(_Symbol,Regime1_RSI_TimeFrame_1,Regime1_RSI_Period_1,Regime1_RSI_Price_1);
         ArraySetAsSeries(Regime1_RSI_1,true);
        }
      if(Regime1_Use_RSI_Confluence_2)
        {
         Hndl_Regime1_RSI_2 = iRSI(_Symbol,Regime1_RSI_TimeFrame_2,Regime1_RSI_Period_2,Regime1_RSI_Price_2);
         ArraySetAsSeries(Regime1_RSI_2,true);
        }
   
      if(Regime1_Use_ADX_Confluence_1)
        {
         Hndl_Regime1_ADX_1 = iADX(_Symbol,Regime1_ADX_Timeframe_1,Regime1_ADX_Period_1);
         ArraySetAsSeries(Regime1_ADX_1,true);
         if(Regime1_Use_ADX_MA_Smoothing_1)
           {
            Regime1_Hndl_MA_ADX_1 = iMA(_Symbol,Regime1_ADX_Timeframe_1,Regime1_ADX_MA_Period_1,0,Regime1_ADX_MA_Type_1,Hndl_Regime1_ADX_1);
            ArraySetAsSeries(Regime1_MA_ADX_1,true);
           }
        }
      if(Regime1_Use_ADX_Confluence_2)
        {
         Hndl_Regime1_ADX_2 = iADX(_Symbol,Regime1_ADX_Timeframe_2,Regime1_ADX_Period_2);
         ArraySetAsSeries(Regime1_ADX_2,true);
         if(Regime1_Use_ADX_MA_Smoothing_2)
           {
            Regime1_Hndl_MA_ADX_2 = iMA(_Symbol,Regime1_ADX_Timeframe_2,Regime1_ADX_MA_Period_2,0,Regime1_ADX_MA_Type_2,Hndl_Regime1_ADX_2);
            ArraySetAsSeries(Regime1_MA_ADX_2,true);
           }
        }
   }




   Hndl_ATR_SL = iCustom(_Symbol,ATRFilterTF, "ATR_Per_Indicator","",ATRFilterPeriod);
   ArraySetAsSeries(ATR_SL, true);

   if(Enable_Higher_TF_ATR_Filter)
     {
      Hndl_ATR_Filter_HTF = iCustom(_Symbol,Higher_TF_ATR_Timeframe,"ATR_Per_Indicator","",Higher_TF_ATR_Period);
      ArraySetAsSeries(ATR_Filter_HTF,true);

     }

   if(Use_ATR_Daily_Restriction)
     {
      Hndl_Daily_ATR_Rest = iCustom(_Symbol,ATR_Daily_Restriction_TimeFrame,"ATR_Per_Indicator","",ATR_Daily_Restriction_Period);
      ArraySetAsSeries(ATR_Daily_Rest,true);
     }

   if(ATR_Perc_OvreRide_Trail)
     {
      Hndl_ATR_PERC_OverRide = iCustom(_Symbol,ATR_Perc_OverRide_TF,"ATR_Per_Indicator");
      ArraySetAsSeries(ATR_PERC_OverRide,true);
     }



   Magic_1 = eamagic;
   Magic_2 = eamagic;
   Magic_3 = eamagic;
   Magic_Addon = eamagic+346382;




   if(RSI_OverBought_Filter)
     {
      RSI_Res_Handle = iRSI(_Symbol,RSI_Res_TF,RSI_Period_Res,RSI_Res_AppliedPrice);
      ArraySetAsSeries(RSI_Res,true);
     }
//---
   if(use_basema1)
      ma1_h = iMA(NULL, basema1_tf, basema1_p, 0, basema1_mode, basema1_price);
   if(use_basema2)
      ma2_h = iCustom(NULL, basema2_tf, "Supertrend_VF", basema2_p, basema2_m);

   if(use_basema5)
      ma5_h = iCustom(NULL, basema5_tf, "Supertrend_VF", basema5_p, basema5_m);



   if(use_basema3)
      ma3_h = iMA(NULL, basema3_tf, basema3_p, 0, basema3_mode, basema3_price);

   if(use_basema4)
      ma4_h = iMA(NULL, basema4_tf, basema4_p, 0, basema4_mode, basema4_price);

  if(Enable_Comparison_Master)
  {
   if(Check_comp_ma)
      comp_ma_h = iMA(comp_symbol, comp_ma_tf, comp_ma_p, 0, comp_ma_mode, comp_ma_price);
   if(Check_comp_st)
      comp_st_h = iCustom(comp_symbol, comp_st_tf, "Supertrend", comp_st_p, comp_st_m);

   if(Check_comp_rsi_1)
     {
      comp_rsi_h_1 = iRSI(comp_symbol,RSI_Comp_TF_1,RSI_Period_Comp_1,RSI_Comp_AppliedPrice_1);
      ArraySetAsSeries(comp_rsi_1,true);
     }
   if(Check_comp_rsi_2)
     {
      comp_rsi_h_2 = iRSI(comp_symbol,RSI_Comp_TF_2,RSI_Period_Comp_2,RSI_Comp_AppliedPrice_2);
      ArraySetAsSeries(comp_rsi_2,true);
     }

   if(Comp_Use_ADX_1)
     {
      Hndl_Comp_ADX_1 = iADX(comp_symbol,Comp_ADX_Timeframe_1,Comp_ADX_Period_1);
      ArraySetAsSeries(Comp_ADX_1,true);
      if(Comp_Use_ADX_MA_Smoothing_1)
        {
         Comp_Hndl_MA_ADX_1 = iMA(comp_symbol,Comp_ADX_Timeframe_1,Comp_ADX_MA_Period_1,0,Comp_ADX_MA_Type_1,Hndl_Comp_ADX_1);
         ArraySetAsSeries(Comp_MA_ADX_1,true);
        }
     }
   if(Comp_Use_ADX_2)
     {
      Hndl_Comp_ADX_2 = iADX(comp_symbol,Comp_ADX_Timeframe_2,Comp_ADX_Period_2);
      ArraySetAsSeries(Comp_ADX_2,true);
      if(Comp_Use_ADX_MA_Smoothing_2)
        {
         Comp_Hndl_MA_ADX_2 = iMA(comp_symbol,Comp_ADX_Timeframe_2,Comp_ADX_MA_Period_2,0,Comp_ADX_MA_Type_2,Hndl_Comp_ADX_2);
         ArraySetAsSeries(Comp_MA_ADX_2,true);
        }
     }
   }

   ArraySetAsSeries(st1, true);
   ArraySetAsSeries(st2, true);
   ArraySetAsSeries(st3, true);

   atrpct_h = iCustom(Symbol(), exec_tf, "ATR_Per_Indicator","");
   ArraySetAsSeries(atrpct, true);




   tm_h = 0;
   tmr = 0;
   NewsInintialization();


   Create_DashBaord();
   
   //Get_Buy_Dynamic_SL(SymbolInfoDouble(_Symbol,SYMBOL_ASK));
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
   ObjectsDeleteAll(0,"News");
   
   //=== COC Dashboard Cleanup ===
   if(Enable_COC_Dashboard && coc_ea_initialized)
   {
       // Send final status update
       string url = COC_Backend_URL + "/api/ea/status/" + coc_instance_uuid;
       string headers = "Content-Type: application/json\r\n";
       
       string json = "{";
       json += "\"status\":\"STOPPED\",";
       json += "\"reason\":\"" + IntegerToString(reason) + "\",";
       json += "\"final_profit\":" + DoubleToString(coc_total_profit, 2) + ",";
       json += "\"total_trades\":" + IntegerToString(coc_total_trades) + ",";
       json += "\"max_drawdown\":" + DoubleToString(coc_max_drawdown, 2) + ",";
       json += "\"last_update\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"";
       json += "}";
       
       char post_data[];
       char result[];
       string result_headers;
       
       StringToCharArray(json, post_data, 0, StringLen(json));
       
       int timeout = 3000;
       int response_code = WebRequest("PUT", url, headers, timeout, post_data, result, result_headers);
       
       if(response_code == 200)
           Print("✅ COC Dashboard: Final status sent successfully");
       else
           Print("⚠️ COC Dashboard: Failed to send final status");
           
       // Export final data
       COC_ExportDataToJSON();
       
       Print("🏁 COC Dashboard: EA shutdown completed - Reason: ", reason);
   }
   
   EventKillTimer();
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkProcessingTime()
  {
   datetime t=TimeCurrent();

   string en = "";
   if(noprocessing_time_start_minute < 10)
     {
      en = IntegerToString(noprocessing_time_start_hour)+":0"+IntegerToString(noprocessing_time_start_minute);
     }
   else
     {
      en = IntegerToString(noprocessing_time_start_hour)+":"+IntegerToString(noprocessing_time_start_minute);
     }

   datetime start_time=StringToTime(TimeToString(t, TIME_DATE)+" "+en);


   string en1 = "";
   if(noprocessing_time_end_minute < 10)
     {
      en1 = IntegerToString(noprocessing_time_end_hour)+":0"+IntegerToString(noprocessing_time_end_minute);
     }
   else
     {
      en1 = IntegerToString(noprocessing_time_end_hour)+":"+IntegerToString(noprocessing_time_end_minute);
     }

   datetime end_time=StringToTime(TimeToString(t, TIME_DATE)+" "+en1);



   if((TimeCurrent() >= start_time  && TimeCurrent() <= end_time))
     {
      return true;
     }

   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkTimeEnd()
  {
   datetime t=TimeCurrent();

   string en = "";
   if(noprocessing_time_end_minute < 10)
     {
      en = IntegerToString(noprocessing_time_end_hour)+":0"+IntegerToString(noprocessing_time_end_minute);
     }
   else
     {
      en = IntegerToString(noprocessing_time_end_hour)+":"+IntegerToString(noprocessing_time_end_minute);
     }

   datetime end_time=StringToTime(TimeToString(t, TIME_DATE)+" "+en);

   datetime end_limit = end_time + 60*5;


   if((TimeCurrent() >= end_time  && TimeCurrent() <= end_limit))
     {

      return true;
     }

   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void RemoveSLTP()
  {
   for(int i = OrdersTotal()-1 ; i>=0 ; i--)
     {
      if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
        {
         if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3)  && OrderSymbol() == _Symbol)
           {

            if(OrderStopLoss()!=0 && OrderTakeProfit()!=0)
              {
               Print("Modifying "+OrderTakeProfit() + " OrderMagic "+OrderMagicNumber());
               OrderModify(OrderTicket(),OrderOpenPrice(),0,0,0,0);
               Print("SL - TP Modified to 0 because of No processing Time");
              }
           }
        }
     }

  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkTimeStart()
  {
   datetime t=TimeCurrent();

   string en = "";
   if(noprocessing_time_start_minute < 10)
     {
      en = IntegerToString(noprocessing_time_start_hour)+":0"+IntegerToString(noprocessing_time_start_minute);
     }
   else
     {
      en = IntegerToString(noprocessing_time_start_hour)+":"+IntegerToString(noprocessing_time_start_minute);
     }

   datetime end_time=StringToTime(TimeToString(t, TIME_DATE)+" "+en);

   datetime end_limit = end_time + 60*5;


   if((TimeCurrent() >= end_time  && TimeCurrent() <= end_limit))
     {
      return true;
     }

   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void AddSLTP()
  {
   for(int i = OrdersTotal()-1 ; i>=0 ; i--)
     {
      if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
        {
         if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3)  && OrderSymbol() == _Symbol)
           {
            string comment = OrderComment();
            string outputArray[];
            int arraySize = StringSplit(comment, ',', outputArray);
            string target_SL_points = comment;
            if(arraySize > 0)
              {
               target_SL_points = outputArray[0];
              }

            int sl_points = StringToInteger(target_SL_points);


            if(OrderStopLoss()==0 && OrderTakeProfit()==0)
              {
               if(OrderType() == OP_BUY)
                 {
                  double sl_level = OrderOpenPrice()-sl_points*_Point;
                  sl_level = NormalizeDouble(sl_level, _Digits);
                  double tp_level = NormalizeDouble(OrderOpenPrice()+(tp_mult_1*sl_points)*_Point, _Digits);

                  double close_price = OrderClosePrice();
                  if(OrderClosePrice() > sl_level && OrderClosePrice() < tp_level)
                    {
                     OrderModify(OrderTicket(),OrderOpenPrice(),sl_level,tp_level,0,0);

                     Print("SL - TP Modified back");
                    }
                  else
                     if(OrderClosePrice() <= sl_level)
                       {

                        bool f = OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20);
                        Print("SL passed so closing trade");

                       }
                     else
                        if(OrderClosePrice() >= tp_level)
                          {
                           bool f = OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20);
                           Print("TP passed so closing trade");
                          }


                 }
               if(OrderType() == OP_SELL)
                 {
                  double sl_level = OrderOpenPrice()+sl_points*_Point;
                  sl_level = NormalizeDouble(sl_level, _Digits);
                  double tp_level = NormalizeDouble(OrderOpenPrice()-(tp_mult_1*sl_points)*_Point, _Digits);

                  double close_price = OrderClosePrice();
                  if(OrderClosePrice() < sl_level && OrderClosePrice() > tp_level)
                    {
                     OrderModify(OrderTicket(),OrderOpenPrice(),sl_level,tp_level,0,0);

                     Print("SL - TP Modified back");
                    }
                  else
                     if(OrderClosePrice() >= sl_level)
                       {

                        bool f = OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20);
                        Print("SL passed so closing trade");

                       }
                     else
                        if(OrderClosePrice() <= tp_level)
                          {
                           bool f = OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20);
                           Print("TP passed so closing trade");
                          }


                 }
              }
           }
        }
     }

  }



datetime tmee;
datetime tm_cur;
datetime tm_daily;

datetime tm_st;
datetime tm_default;

datetime tm_d_atr_res;
datetime tm_atr_filter;



datetime tm_trail_bb;
datetime tm_trail_rsi;
datetime tm_trail_atr_override_exp;







//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Inside_Bar_Post_Trailing()
  {

  }




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
datetime tm_posttp_insidebar_exit;

void OnTick()
  {
   //=== COC Dashboard Integration in OnTick ===
   if(Enable_COC_Dashboard)
   {
       // Check for remote commands
       COC_CheckForCommands();
       
       // Send status updates
       COC_SendStatusUpdate();
       
       // Export data to JSON files
       COC_ExportDataToJSON();
       
       // Check if trading is paused by COC
       if(coc_is_paused)
       {
           return; // Skip trading logic if paused by COC
       }
       
       // Check if remote trading is disabled
       if(!coc_remote_trading_enabled && coc_remote_control_active)
       {
           return; // Skip trading logic if disabled remotely
       }
   }
   
   if(standard_red_news)
   {
    return;
   }
   Expire_AddOn_Pend();
   AddOn_Trailing();
   if(tm_cur!=iTime(_Symbol,_Period,0))
   {
    Candle_Based_BE();
    tm_cur  = iTime(_Symbol,_Period,0);
   }
   Get_ATR_Percentage_Override_Mult(ATR_Perc_OvreRide_MultiPlier);
   Get_BB_Trailing_Min_SL_Mult(BB_Trailing_Min_SL_Mult);
   Get_RSI_Trailing_Min_SL_Mult(RSI_Trailing_Min_SL_Mult);
   Get_Structure_SL_Mult(Trailing_Stop_Min_SL_Multiplier);

   if(tm_posttp_insidebar_exit!=iTime(_Symbol,Price_Structure_TF,0))
   {
    PostTP_InsideBar_Exit();
    tm_posttp_insidebar_exit = iTime(_Symbol,Price_Structure_TF,0);
   }

   if(tm_trail_bb!=iTime(_Symbol,BB_Trailing_Cnd_TF,0))
     {
      BB_Trail();
      tm_trail_bb = iTime(_Symbol,BB_Trailing_Cnd_TF,0);
     }
   if(BB_Trail_Method == Trigger_On_Cross)
   {
      BB_Trail(); 
   }

   if(tm_trail_rsi!=iTime(_Symbol,RSI_Trailing_Cnd_TF,0))
     {
      RSI_Trail();
      tm_trail_rsi = iTime(_Symbol,RSI_Trailing_Cnd_TF,0);
     }
   if(RSI_Trail_Method == Trigger_On_Cross)
   {
      RSI_Trail(); 
   }
   if(ATR_Trailing_Trigger_Method == OnCross || tm_trail_atr_override_exp!=iTime(_Symbol,Trailing_Stop_Candle_TF,0))
     {
      Trailing_Atr_Expansion_Based();
      tm_trail_atr_override_exp = iTime(_Symbol,Trailing_Stop_Candle_TF,0);
     }


   Trailing_Atr_Expansion_Based();

//-------------------------------------------------------------------------------//
//------------------------------------------------------------------------------//
   if(tm_atr_filter!=iTime(_Symbol,ATRFilterTF,0))
     {
      CopyBuffer(Hndl_ATR_SL,0,0,10,ATR_SL);
      tm_atr_filter = iTime(_Symbol,ATRFilterTF,0);
     }

   if(Use_ATR_Daily_Restriction)
     {
      if(tm_d_atr_res!=iTime(_Symbol,ATR_Daily_Restriction_TimeFrame,0))
        {
         CopyBuffer(Hndl_Daily_ATR_Rest,0,0,10,ATR_Daily_Rest);
         tm_d_atr_res = iTime(_Symbol,ATR_Daily_Restriction_TimeFrame,0);
        }
     }


   if(RSI_OverBought_Filter)
     {
      CopyBuffer(RSI_Res_Handle,0,0,No_Of_Candles_To_Reset_RSI+2,RSI_Res);
     }




   bool buy_ma = false;
   bool sell_ma = false;
   CheckMA(buy_ma, sell_ma);



   bool processing_ok = true;
   if(use_time_filter_noprocessing)
      processing_ok = !IsTimeWithinLimits(noprocessing_time_start_hour, noprocessing_time_start_minute, noprocessing_time_end_hour, noprocessing_time_end_minute);



   if(use_time_filter_noprocessing)
     {
      if(checkTimeStart())
        {
         RemoveSLTP();
        }

      if(checkTimeEnd())
        {
         AddSLTP();
         ProcessExits();
        }

      if(checkProcessingTime() == false)
        {
         if(tmee!=iTime(_Symbol,PERIOD_M5,1))
           {
            AddSLTP();
            tmee=iTime(_Symbol,PERIOD_M5,1);
           }
         ProcessExits();
        }

     }
   else
     {
      ProcessExits();
     }




   Ask = SymbolInfoDouble(Symbol(), SYMBOL_ASK);
   Bid = SymbolInfoDouble(Symbol(), SYMBOL_BID);


   if(use_friday_closing)
     {
      if(IsWeekday(FRIDAY) && IsTimeWithinLimits(fridayclosing_time_start_hour, fridayclosing_time_start_minute, 23, 59))
        {
         CloseAll();
         CloseAllOrders();
         return;
        }
     }
   if(use_everyday_closing)
     {
      if(IsTimeWithinLimits(everydayclosing_time_start_hour, everydayclosing_time_start_minute, 23, 59))
        {
         CloseAll();
         CloseAllOrders();
         return;
        }
     }
   if(use_week_reset)
      if(WReset())
         return;


   bool trades_ok = true;
   if(use_time_filter_notrades)
      trades_ok = !IsTimeWithinLimits(notrades_time_start_hour, notrades_time_start_minute, notrades_time_end_hour, notrades_time_end_minute);
   if(!DaysFilter(TimeCurrent()))
      trades_ok = false;
   if(!processing_ok)
      trades_ok = false;

   bool orders_time_ok = trades_ok;
   if(orders_time_ok && use_time_filter_signals)
      orders_time_ok = IsTimeWithinLimits(signal_time_start_hour, signal_time_start_minute, signal_time_end_hour, signal_time_end_minute);

   if(!orders_time_ok)
     {
      CloseAllOrders();
      return;
     }

   UpdateBuffers();



   if(tm_default!=iTime(_Symbol,Default_Candle_TimeFrame,0))
     {
      bool draw = false;
      if(ObjectFind(0,"Rng_Box")>=0)
        {
         datetime rng_box_end_time = datetime(MathMax(ObjectGetInteger(0,"Rng_Box",OBJPROP_TIME,0),ObjectGetInteger(0,"Rng_Box",OBJPROP_TIME,1)));
         if(iBarShift(_Symbol,Default_Candle_TimeFrame,rng_box_end_time) >= 1)
           {
            draw = true;
           }
        }
      else
        {
         draw = true;
        }
      if(draw)
        {
         Close_Pending_ALL();
         double Range_Hi = 0;
         double Range_Lo = 0;

         Draw_Rng_Box(Range_Hi,Range_Lo);

         if(Check_Confuluence() &&  Check_Friday_Trades())
           {

            if(Check_Comp_Sell() && (trademode != buy_only  && sell_ma))
              {
               MakeSell("stop",Range_Lo);
              }
            if(Check_Comp_Buy() && (trademode != sell_only  && buy_ma))
              {
               MakeBuy("stop",Range_Hi);
              }
           }

        }

      tm_default = iTime(_Symbol,Default_Candle_TimeFrame,0);
     }

   if(Tot_Trades(OP_BUY,OP_BUYSTOP) == 0 && Max_No_Of_Trades_On_Current_Candle(OP_BUY)<Maximum_No_Of_Trades_On_BO_Cand && Last_Trade_Close_In_Loss(OP_BUY))
     {
      if(ObjectFind(0,"Rng_Box")>=0)
        {
         double rng_hi = MathMax(ObjectGetDouble(0,"Rng_Box",OBJPROP_PRICE,0),ObjectGetDouble(0,"Rng_Box",OBJPROP_PRICE,1));
         MakeBuy("stop",rng_hi);
        }
     }
   if(Tot_Trades(OP_SELL,OP_SELLSTOP) == 0 && Max_No_Of_Trades_On_Current_Candle(OP_SELL)<Maximum_No_Of_Trades_On_BO_Cand && Last_Trade_Close_In_Loss(OP_SELL))
     {
      if(ObjectFind(0,"Rng_Box")>=0)
        {
         double rng_lo = MathMin(ObjectGetDouble(0,"Rng_Box",OBJPROP_PRICE,0),ObjectGetDouble(0,"Rng_Box",OBJPROP_PRICE,1));
         MakeSell("stop",rng_lo);
        }
     }
     AdOn_Trade();
     
     
     Update_DashBoards();
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double OnTester()
  {
   double ret=0;


   if(TesterStatistics(STAT_TRADES) < 10)
      return(0);



   return(TesterStatistics(STAT_CUSTOM_ONTESTER));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool checkSpread()
  {
   if(!Enable_Spread_Protection)
     {
      return true;
     }
   int current_spread_points = SymbolInfoInteger(_Symbol,SYMBOL_SPREAD);
   int max_spread_points = Max_Spread_Pips * 10;
   if(current_spread_points>=max_spread_points)
     {
      if(Log_Spred_Blocks)
        {
         Print(" Trade BLocked Due To Spread Curren Spread Points ",current_spread_points," Max Spread Points ",max_spread_points);
        }
      return false;
     }
   return true;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_Risk_Money_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  Risked_Money_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  Risked_Money_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  =  Risked_Money_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  Risked_Money_Multiplier_Expansion;
     }
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_TP_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  tp_mult_1*TP_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  tp_mult_1*TP_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  =  tp_mult_1*TP_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  tp_mult_1*TP_Multiplier_Expansion;
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_ATR_Percentage_Override_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  ATR_Perc_OvreRide_MultiPlier_*ATR_Percentage_Override_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  ATR_Perc_OvreRide_MultiPlier_*ATR_Percentage_Override_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  =  ATR_Perc_OvreRide_MultiPlier_*ATR_Percentage_Override_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  ATR_Perc_OvreRide_MultiPlier_*ATR_Percentage_Override_Multiplier_Expansion;
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_BB_Trailing_Min_SL_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  BB_Trailing_Min_SL_Mult_*BB_Trailing_Min_SL_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  BB_Trailing_Min_SL_Mult_*BB_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  =  BB_Trailing_Min_SL_Mult_*BB_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  BB_Trailing_Min_SL_Mult_*BB_Trailing_Min_SL_Multiplier_Expansion;
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_RSI_Trailing_Min_SL_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  RSI_Trailing_Min_SL_Mult_*RSI_Trailing_Min_SL_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  RSI_Trailing_Min_SL_Mult_*RSI_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  = RSI_Trailing_Min_SL_Mult_*RSI_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  RSI_Trailing_Min_SL_Mult_*RSI_Trailing_Min_SL_Multiplier_Expansion;
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
/*
void Get_Structure_SL_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  Structure_SL_Multiplier_Compression;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  Structure_SL_Multiplier_Mixed_C2_In_C1_Out;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  = Structure_SL_Multiplier_Mixed_C2_Out_C1_In;
     }
   if(Is_In_Expansion())
     {
      val  =  Structure_SL_Multiplier_Expansion;
     }
  }
  */
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Get_Structure_SL_Mult(double &val)
  {
   if(Is_In_Compreesion())
     {
      val =  Structure_SL_Multiplier_Compression * Trailing_Stop_Min_SL_Multiplier_;
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      val  =  Structure_SL_Multiplier_Mixed_C2_In_C1_Out * Trailing_Stop_Min_SL_Multiplier_;
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      val  = Structure_SL_Multiplier_Mixed_C2_Out_C1_In * Trailing_Stop_Min_SL_Multiplier_;
     }
   if(Is_In_Expansion())
     {
      val  =  Structure_SL_Multiplier_Expansion * Trailing_Stop_Min_SL_Multiplier_;
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Is_In_Compreesion()
  {
   if(Enable_CandleRange_Logic && Enable_Compression_Mode_C1_C2)
     {
      double hi1 = iHigh(_Symbol,Candle_1_TimeFrame,1);
      double lo1 = iLow(_Symbol,Candle_1_TimeFrame,1);
      double hi2 = iHigh(_Symbol,Candle_2_TimeFrame,1);
      double lo2 = iLow(_Symbol,Candle_2_TimeFrame,1);
      double prc = iClose(_Symbol,_Period,0);
      if(prc<=hi1 && prc>=lo1 && prc<=hi2 && prc>=lo2)
        {
         return true;
        }
     }
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Is_In_Mixed_C2In_C1Out()
  {
   if(Enable_CandleRange_Logic && Enable_Mixed_Mode_C2_Inside_C1_Outside)
     {
      double hi1 = iHigh(_Symbol,Candle_1_TimeFrame,1);
      double lo1 = iLow(_Symbol,Candle_1_TimeFrame,1);
      double hi2 = iHigh(_Symbol,Candle_2_TimeFrame,1);
      double lo2 = iLow(_Symbol,Candle_2_TimeFrame,1);
      double prc = iClose(_Symbol,_Period,0);
      if((prc>hi1 || prc<lo1) && (prc<=hi2 && prc>=lo2))
        {
         return true;
        }
     }
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Is_In_Mixed_C2Out_C1In()
  {
   if(Enable_CandleRange_Logic && Enable_Mixed_Mode_C2_Outside_C1_Inside)
     {
      double hi1 = iHigh(_Symbol,Candle_1_TimeFrame,1);
      double lo1 = iLow(_Symbol,Candle_1_TimeFrame,1);
      double hi2 = iHigh(_Symbol,Candle_2_TimeFrame,1);
      double lo2 = iLow(_Symbol,Candle_2_TimeFrame,1);
      double prc = iClose(_Symbol,_Period,0);
      if((prc<=hi1 && prc>=lo1) && (prc>hi2 || prc<lo2))
        {
         return true;
        }
     }
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Is_In_Expansion()
  {
   if(Enable_CandleRange_Logic && Enable_Expansion_Mode_C1_C2)
     {
      double hi1 = iHigh(_Symbol,Candle_1_TimeFrame,1);
      double lo1 = iLow(_Symbol,Candle_1_TimeFrame,1);
      double hi2 = iHigh(_Symbol,Candle_2_TimeFrame,1);
      double lo2 = iLow(_Symbol,Candle_2_TimeFrame,1);
      double prc = iClose(_Symbol,_Period,0);
      if((prc>hi1 || prc<lo1) && (prc>hi2 || prc<lo2))
        {
         return true;
        }
     }
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Consec_Streak()
  {
   if(!Enable_Streak_Trigger)
     {
      return true;
     }
   int win_cnt = 0;
   int loss_cnt = 0;
   for(int i=OrdersHistoryTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)==true)
        {
         if((OrderCloseTime()>=iTime(_Symbol,Reset_TF,0)) && (OrderType() == OP_BUY || OrderType() == OP_SELL) && OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderProfit()+OrderCommission()+OrderSwap())>0)
              {
               win_cnt++;
               loss_cnt = 0;
              }
            if((OrderProfit()+OrderCommission()+OrderSwap())<0)
              {
               loss_cnt++;
               win_cnt = 0;
              }
            if(loss_cnt>=Max_Consecutive_SL_Streak || win_cnt>=Max_Consecutive_TP_Streak)
              {
               return false;
              }
           }
        }
     }
   return true;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_monday_fiter()
  {
   MqlDateTime date;
   TimeToStruct(TimeCurrent(), date);
   int day = date.day_of_week;
   if(!Enable_Monday_Trading_Filter || day !=1)
     {
      return true;
     }
   datetime t = StringToTime(TimeToString(TimeCurrent(), TIME_DATE)+" "+Monday_Trading_Start_Hour);
   if(TimeCurrent()>t)
     {
      return true;
     }
   return false;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void BB_Trail()
  {
   if(!Use_BB_Trailing)
     {
      return;
     }

   CopyBuffer(Hndl_BB_Trail,1,0,10,BB_Trail_UP);
   CopyBuffer(Hndl_BB_Trail,2,0,10,BB_Trail_DN);

   bool Band_Touch = false;
   if(BB_Trail_Method == Trigger_On_Close)
   {
     Band_Touch = (iHigh(_Symbol,BB_Trailing_TF,1) > BB_Trail_UP[1] && iLow(_Symbol,BB_Trailing_TF,1) < BB_Trail_UP[1]) || (iHigh(_Symbol,BB_Trailing_TF,1) > BB_Trail_DN[1] && iLow(_Symbol,BB_Trailing_TF,1) < BB_Trail_DN[1]);
   }
   if(BB_Trail_Method == Trigger_On_Cross)
   {
     Band_Touch = (iHigh(_Symbol,BB_Trailing_TF,0) > BB_Trail_UP[0] && iLow(_Symbol,BB_Trailing_TF,0) < BB_Trail_UP[0]) || (iHigh(_Symbol,BB_Trailing_TF,0) > BB_Trail_DN[0] && iLow(_Symbol,BB_Trailing_TF,0) < BB_Trail_DN[0]);
   }
   
   bool Cnd_Conf = false;
   if(BB_Trail_Method == Trigger_On_Close)
   {
      if(BB_Trailing_Cnd_Col == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(BB_Trailing_Cnd_Col == Cand_Green && iClose(_Symbol,BB_Trailing_Cnd_TF,1)>iOpen(_Symbol,BB_Trailing_Cnd_TF,1))
        {
         Cnd_Conf = true;
        }
      if(BB_Trailing_Cnd_Col == Cand_Red && iClose(_Symbol,BB_Trailing_Cnd_TF,1)<iOpen(_Symbol,BB_Trailing_Cnd_TF,1))
        {
         Cnd_Conf = true;
        }
   } 
   if(BB_Trail_Method == Trigger_On_Cross)
   {
      if(BB_Trailing_Cnd_Col == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(BB_Trailing_Cnd_Col == Cand_Green && iClose(_Symbol,BB_Trailing_Cnd_TF,0)>iOpen(_Symbol,BB_Trailing_Cnd_TF,0))
        {
         Cnd_Conf = true;
        }
      if(BB_Trailing_Cnd_Col == Cand_Red && iClose(_Symbol,BB_Trailing_Cnd_TF,0)<iOpen(_Symbol,BB_Trailing_Cnd_TF,0))
        {
         Cnd_Conf = true;
        }
   } 
   if(Band_Touch && Cnd_Conf)
     {
      for(int i =OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderSymbol() == _Symbol) && (OrderType() == OP_BUY || OrderType() == OP_SELL) && (OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3))
              {
               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }
               int sl_points = StringToInteger(target_SL_points);
               if(OrderType() == OP_BUY)
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                  double expected_profit = sl_points*BB_Trailing_Min_SL_Mult;
                  if(profit >= expected_profit)
                    {
                     double new_sl = 0;
                     
                     if(BB_Trail_Type == Trail_By_Candle)
                     {
                      new_sl = NormalizeDouble(iLow(NULL, BB_Trailing_Cnd_TF, 1)*(1-BB_Trailing_Candle_Percentage/100), _Digits);
                     }
                     if(BB_Trail_Type == Trail_By_Percent)
                     {
                      new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)*(1-BB_Trailing_Price_Percentage/100), _Digits); 
                     }
                     
                     if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"BB Trailing New SL "+new_sl);
                           if(Journal_BB_Trailing)
                             {
                              Print("   Bollinger Bands Trailing ");
                              //Print(BB_Trail_UP[1],"   ",BB_Trail_DN[1],"  expected_profit  ",expected_profit);
                              //ExpertRemove();
                             }
                          }
                       }
                    }
                 }
               if(OrderType()==OP_SELL)
                 {
                  double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                  double expected_profit = sl_points*BB_Trailing_Min_SL_Mult;
                  if(profit >= expected_profit)
                    {
                     double new_sl = 0;
                     if(BB_Trail_Type == Trail_By_Candle)
                     {
                      new_sl = NormalizeDouble(iHigh(NULL, BB_Trailing_Cnd_TF, 1)*(1+BB_Trailing_Candle_Percentage/100), _Digits);
                     }
                     if(BB_Trail_Type == Trail_By_Percent)
                     {
                      new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)*(1+BB_Trailing_Price_Percentage/100), _Digits);
                     }
                     if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"BB Trailing New SL "+new_sl);
                           if(Journal_BB_Trailing)
                             {
                              Print("   Bollinger Bands Trailing ");
                              //  ExpertRemove();
                             }
                          }
                       }
                    }
                 }
              }
           }
        }
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void RSI_Trail()
  {
   if(!Use_RSI_Trailing)
     {
      return;
     }
   CopyBuffer(Hndl_RSI_Trail,0,0,10,RSI_Trail_Buffer);


   bool Trail_Long = false;
   bool Trail_Short = false;
   
   if(RSI_Trail_Method == Trigger_On_Close)
   {
       Trail_Long = RSI_Trail_Buffer[1]>RSI_Trailing_Threshold_Long;
       Trail_Short = RSI_Trail_Buffer[1]<RSI_Trailing_Threshold_Short;
   }
   if(RSI_Trail_Method == Trigger_On_Cross)
   {
       Trail_Long = RSI_Trail_Buffer[0]>RSI_Trailing_Threshold_Long;
       Trail_Short = RSI_Trail_Buffer[0]<RSI_Trailing_Threshold_Short;
   }   

   bool Cnd_Conf = false;
   if(RSI_Trail_Method == Trigger_On_Close)
   {
      if(RSI_Trailing_Cnd_Col == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(RSI_Trailing_Cnd_Col == Cand_Green && iClose(_Symbol,RSI_Trailing_Cnd_TF,1)>iOpen(_Symbol,RSI_Trailing_Cnd_TF,1))
        {
         Cnd_Conf = true;
        }
      if(RSI_Trailing_Cnd_Col == Cand_Red && iClose(_Symbol,RSI_Trailing_Cnd_TF,1)<iOpen(_Symbol,RSI_Trailing_Cnd_TF,1))
        {
         Cnd_Conf = true;
        }
   } 
   if(RSI_Trail_Method == Trigger_On_Close)
   {
      if(RSI_Trailing_Cnd_Col == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(RSI_Trailing_Cnd_Col == Cand_Green && iClose(_Symbol,RSI_Trailing_Cnd_TF,0)>iOpen(_Symbol,RSI_Trailing_Cnd_TF,0))
        {
         Cnd_Conf = true;
        }
      if(RSI_Trailing_Cnd_Col == Cand_Red && iClose(_Symbol,RSI_Trailing_Cnd_TF,0)<iOpen(_Symbol,RSI_Trailing_Cnd_TF,0))
        {
         Cnd_Conf = true;
        }
   }    
   if(Cnd_Conf)
     {
      for(int i =OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderSymbol() == _Symbol) && (OrderType() == OP_BUY || OrderType() == OP_SELL) && (OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3))
              {
               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }
               int sl_points = StringToInteger(target_SL_points);
               if(OrderType() == OP_BUY && Trail_Long)
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                  double expected_profit = sl_points*RSI_Trailing_Min_SL_Mult;
                  if(profit >= expected_profit)
                    {
                     double new_sl = 0;
                     if(RSI_Trail_Type == Trail_By_Candle)
                     {
                      new_sl = NormalizeDouble(iLow(NULL, RSI_Trailing_Cnd_TF, 1)*(1-RSI_Trailing_Candle_Percentage/100), _Digits);
                     }
                     if(RSI_Trail_Type == Trail_By_Percent)
                     {
                      new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)*(1-RSI_Trailing_Price_Percentage/100), _Digits);
                     }
                     
                     if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"RSI Trailing New SL "+new_sl);
                           if(Journal_RSI_Trailing)
                             {
                              Print("Journal RSI Trailing ");
                              //ExpertRemove();
                             }
                          }
                       }
                    }
                 }
               if(OrderType()==OP_SELL && Trail_Short)
                 {
                  double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                  double expected_profit = sl_points*RSI_Trailing_Min_SL_Mult;
                  if(profit >= expected_profit)
                    {
                     double new_sl = 0;
                     if(RSI_Trail_Type == Trail_By_Candle)
                     {
                       new_sl = NormalizeDouble(iHigh(NULL, RSI_Trailing_Cnd_TF, 1)*(1+RSI_Trailing_Candle_Percentage/100), _Digits);
                     }
                     if(RSI_Trail_Type == Trail_By_Percent)
                     {
                      new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)*(1+RSI_Trailing_Price_Percentage/100), _Digits);
                     }
                     if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"RSI Trailing New SL "+new_sl);
                           if(Journal_RSI_Trailing)
                             {
                              Print("Journal RSI Trailing ");
                              //ExpertRemove();
                             }
                          }
                       }
                    }
                 }
              }
           }
        }
     }
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Trailing_Atr_Expansion_Based()
  {
   if(!ATR_Trailing_Override_Enabled)
     {
      return;
     }
   double buy_trail_trigger_price = 0;
   double sell_trail_trigger_price = 0;
   for(int i = 1; i<=ATR_Trailing_Candle_Count; i++)
     {
      if(ATR_Trailing_PriceCross_Type == HighLow)
        {
         buy_trail_trigger_price = buy_trail_trigger_price + iHigh(_Symbol,ATR_Trailing_Override_Timeframe,i);
         sell_trail_trigger_price = sell_trail_trigger_price + iLow(_Symbol,ATR_Trailing_Override_Timeframe,i);
        }
      if(ATR_Trailing_PriceCross_Type == OpenCloseMax)
        {
         buy_trail_trigger_price =  buy_trail_trigger_price + MathMax(iOpen(_Symbol,ATR_Trailing_Override_Timeframe,i),iClose(_Symbol,ATR_Trailing_Override_Timeframe,i));
         sell_trail_trigger_price = sell_trail_trigger_price + MathMin(iOpen(_Symbol,ATR_Trailing_Override_Timeframe,i),iClose(_Symbol,ATR_Trailing_Override_Timeframe,i));
        }
     }
   buy_trail_trigger_price = (buy_trail_trigger_price/ATR_Trailing_Candle_Count);
   sell_trail_trigger_price = (sell_trail_trigger_price/ATR_Trailing_Candle_Count);
   if(ATR_Trailing_PriceCross_Type == OpenCloseMax)
     {
      buy_trail_trigger_price = buy_trail_trigger_price * ATR_Trailing_Override_Multiplier;
      sell_trail_trigger_price = sell_trail_trigger_price * ATR_Trailing_Override_Multiplier;
     }
   bool price_trigger_buy = false;
   bool price_trigger_sell = false;
   if(ATR_Trailing_Trigger_Method == OnClose && iClose(_Symbol,ATR_Trailing_Override_Timeframe,1)>buy_trail_trigger_price)
     {
      price_trigger_buy = true;
     }
   if(ATR_Trailing_Trigger_Method == OnCross && iHigh(_Symbol,ATR_Trailing_Override_Timeframe,0)>buy_trail_trigger_price)
     {
      price_trigger_buy = true;
     }
   if(ATR_Trailing_Trigger_Method == OnClose && iClose(_Symbol,ATR_Trailing_Override_Timeframe,1)<sell_trail_trigger_price)
     {
      price_trigger_sell = true;
     }
   if(ATR_Trailing_Trigger_Method == OnCross && iHigh(_Symbol,ATR_Trailing_Override_Timeframe,0)<sell_trail_trigger_price)
     {
      price_trigger_sell = true;
     }
   bool Cnd_Conf = false;
   if(Trailing_Stop_Candle_Colour == Cand_Any)
     {
      Cnd_Conf = true;
     }
   if(Trailing_Stop_Candle_Colour == Cand_Green && iClose(_Symbol,Trailing_Stop_Candle_TF,1)>iOpen(_Symbol,Trailing_Stop_Candle_TF,1))
     {
      Cnd_Conf = true;
     }
   if(Trailing_Stop_Candle_Colour == Cand_Red && iClose(_Symbol,Trailing_Stop_Candle_TF,1)<iOpen(_Symbol,Trailing_Stop_Candle_TF,1))
     {
      Cnd_Conf = true;
     }
   if(Cnd_Conf)
     {
      for(int i = OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol)
              {
               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }
               int sl_points = StringToInteger(target_SL_points);
               if(OrderType() == OP_BUY && price_trigger_buy)
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                  double expected_profit = sl_points*Trailing_Stop_Min_SL_Multiplier;
                  if(profit >= expected_profit)
                    {
                     double new_sl = NormalizeDouble(iLow(NULL, Trailing_Stop_Candle_TF, 1)*(1-Trailing_Stop_ATR_Buffer_Percentage/100), _Digits);
                     if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"Atr Trailing New SL "+new_sl);
                           if(Journal_ATR_Trailing_Override)
                             {
                              Print(" Trailing Atr Expansion Based  ");
                             }
                          }
                       }
                    }
                 }
               else
                  if(OrderType()==OP_SELL && price_trigger_sell)
                    {
                     double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                     double expected_profit = sl_points*Trailing_Stop_Min_SL_Multiplier;
                     if(profit >= expected_profit)
                       {
                        double new_sl = NormalizeDouble(iHigh(NULL, Trailing_Stop_Candle_TF, 1)*(1+Trailing_Stop_ATR_Buffer_Percentage/100), _Digits);
                        if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                             {
                              ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+"Atr Trailing New SL "+new_sl);
                              if(Journal_ATR_Trailing_Override)
                                {
                                 Print("  Trailing Atr Expansion Based  ");
                                }
                             }
                          }
                       }
                    }
              }

           }
        }
     }
  }





//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Friday_Trades()
  {
   if(!No_More_Trade_On_Friday)
     {
      return true;
     }
   datetime t=TimeCurrent();
   datetime time_begin1=StringToTime(TimeToString(t, TIME_DATE)+" "+IntegerToString(Friday_No_New_Trade_Start_Hour)+":"+IntegerToString(Friday_No_New_Trade_Start_Minute));
   if(t>time_begin1)
     {
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Confuluence()
  {
   if(!Enable_Confluence_Master) return true;
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   int cnt_mandatory = 0;
   int cnt_optional = 0; 
   string  mandatory = "";
   string  optional = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   string rsi1 = "RSI1: ";
   string rsi2 = "RSI2: ";
   string adx1 = "ADX1: ";
   string adx2 = "ADX2: ";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   bool rsi1_check = true; 
   bool rsi2_check = true;
   bool adx1_check = true;
   bool adx2_check = true;  
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   if(Regime1_Use_RSI_Confluence_1)
     {
      rsi1_check = false;
      CopyBuffer(Hndl_Regime1_RSI_1,0,0,10,Regime1_RSI_1);
      if(!(Regime1_RSI_1[1]<Regime1_RSI_Minimum_Level_1 || Regime1_RSI_1[1]>Regime1_RSI_Maximum_Level_1));
      {
       // Print("  true   ");
        rsi1_check = true;
        rsi1 = rsi1+" Passed ";
        if(Regime1_RSI_Confluence_1_Mandatory) 
        {
         mandatory = mandatory+"\n"+rsi1;
         cnt_mandatory++;
        }
        else
        {
         optional = optional+"\n"+rsi1;
         cnt_optional++;
        }
      }
      if(Regime1_RSI_Confluence_1_Mandatory &&  !rsi1_check)return false;
     }
     else
     {
        rsi1 = rsi1+" Skipped (Disabled) ";
        if(Regime1_RSI_Confluence_1_Mandatory)mandatory = mandatory+"\n"+rsi1;
        else optional = optional+"\n"+rsi1;
     }
     
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
   if(Regime1_Use_RSI_Confluence_2)
     {
      rsi2_check = false;
      CopyBuffer(Hndl_Regime1_RSI_2,0,0,10,Regime1_RSI_2);
      if(!(Regime1_RSI_2[1]<Regime1_RSI_Minimum_Level_2 || Regime1_RSI_2[1]>Regime1_RSI_Maximum_Level_2))
        {
           rsi2_check = true;
           rsi2 = rsi2+" Passed ";
           if(Regime1_RSI_Confluence_2_Mandatory) 
           {
            mandatory = mandatory+"\n"+rsi2;
            cnt_mandatory++;
           }        
           else
           {
            optional = optional+"\n"+rsi2;
            cnt_optional++;
           }            
        }
        if(Regime1_RSI_Confluence_2_Mandatory &&  !rsi2_check)return false;
     }
     else
     {
      rsi2 = rsi2+" Skipped (Disabled)";
      if(Regime1_RSI_Confluence_2_Mandatory)mandatory = mandatory+"\n"+rsi2;
      else optional = optional+"\n"+rsi2;      
     } 
     if(Regime1_RSI_Confluence_2_Mandatory &&  !rsi2_check)return false;
     
     
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
   if(Regime1_Use_ADX_Confluence_1)
     {
      adx1_check = false;     
      if(Regime1_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Regime1_Hndl_MA_ADX_1,0,0,10,Regime1_MA_ADX_1);
         if(!(Regime1_MA_ADX_1[1]<Regime1_ADX_Minimum_Level_1 || Regime1_MA_ADX_1[1]>Regime1_ADX_Maximum_Level_1))
           {
              adx1_check = true;
              adx1 = adx1+" Passed ";
              if(Regime1_ADX_Confluence_1_Mandatory) 
              {
               mandatory = mandatory+"\n"+adx1;
               cnt_mandatory++;
              }
              else
              {
               optional = optional+"\n"+adx1;
               cnt_optional++;
              }                             
           }
        }
      else
        {
         CopyBuffer(Hndl_Regime1_ADX_1,0,0,10,Regime1_ADX_1);
         if(!(Regime1_ADX_1[1]<Regime1_ADX_Minimum_Level_1 || Regime1_ADX_1[1]>Regime1_ADX_Maximum_Level_1))
           {
            adx1_check = true;
            adx1 = adx1+" Passed "; 
             if(Regime1_ADX_Confluence_1_Mandatory) 
              {
               mandatory = mandatory+"\n"+adx1;
               cnt_mandatory++;
              } 
              else
              {
               optional = optional+"\n"+adx1;
               cnt_optional++;
              }                         
           }
        }
        if(Regime1_ADX_Confluence_1_Mandatory &&  !adx1_check)return false;
     }
     else
     {
      adx1 = adx1+" Skipped (Disabled)";
        if(Regime1_ADX_Confluence_1_Mandatory)mandatory = mandatory+"\n"+adx1;
        else optional = optional+"\n"+adx1;      
     }
    
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+       
   if(Regime1_Use_ADX_Confluence_2)
     {
      adx2_check = false; 
      if(Regime1_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Regime1_Hndl_MA_ADX_2,0,0,10,Regime1_MA_ADX_2);
         if(!(Regime1_MA_ADX_2[1]<Regime1_ADX_Minimum_Level_2 || Regime1_MA_ADX_2[1]>Regime1_ADX_Maximum_Level_2))
           {
            adx2_check = true;
            adx2 = adx2+" Passed ";
            if(Regime1_ADX_Confluence_2_Mandatory) 
             {
               mandatory = mandatory+"\n"+adx2;
               cnt_mandatory++;
             }
              else
              {
               optional = optional+"\n"+adx2;
               cnt_optional++;
              }                            
           }
        }
      else
        {
         CopyBuffer(Hndl_Regime1_ADX_2,0,0,10,Regime1_ADX_2);
         if(!(Regime1_ADX_2[1]<Regime1_ADX_Minimum_Level_2 || Regime1_ADX_2[1]>Regime1_ADX_Maximum_Level_2))
           {
            adx2_check = true;
            adx2 = adx2+" Passed ";
            if(Regime1_ADX_Confluence_2_Mandatory) 
             {
               mandatory = mandatory+"\n"+adx2;
               cnt_mandatory++;
             }
              else
              {
               optional = optional+"\n"+adx2;
               cnt_optional++;
              }            
           }
        }
        if(Regime1_ADX_Confluence_2_Mandatory &&  !adx2_check)return false;
     }
     else
     {
      adx2 = adx2+" Skipped (Disabled)";
      if(Regime1_ADX_Confluence_1_Mandatory)mandatory = mandatory+"\n"+adx2;
      else optional = optional+"\n"+adx2;       
     } 
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+          

   if(cnt_optional>=Confluence_Optional_Minimum_Pass)
   {
    if(Confluence_Enable_Journal)
    {
       Print("==================== [Confluence Check] - Result  TRUE ====================");
       Print(" Mandatory ");
       Print(mandatory);         
       Print(" Optional ");
       Print(optional);  
       Print("Final Decision: Passed("+cnt_mandatory+" mandatory "+cnt_optional+" optional passed");
    }
//    Print("  Big True    ");
    return true;
   }

   return false;
  }




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_atr_restriction(int ord_typ)
  {

   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);

   if(!Use_ATR_Daily_Restriction)
     {
      return true;
     }
   if(ord_typ == OP_BUYSTOP || ord_typ == OP_BUYLIMIT || ord_typ == OP_BUY)
     {
      if(ATR_Daily_Restriction_TimeFrame == PERIOD_D1)
        {
         int i = 0;
         double last_cand_hi = iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
         double threshhold_price = NormalizeDouble(last_cand_hi+ ((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100)*last_cand_hi,digits);
         if(iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i)>threshhold_price)
           {
            return false;
           }
        }
      else
        {
         for(int i = iBarShift(_Symbol,ATR_Daily_Restriction_TimeFrame,iTime(_Symbol,PERIOD_D1,0)) ; i>0; i--)
           {
            double last_cand_hi = iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
            double threshhold_price = NormalizeDouble(last_cand_hi+ ((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100)*last_cand_hi,digits);
            if(iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i)>threshhold_price)
              {
               return false;
              }
           }
        }
     }
   if(ord_typ == OP_SELLSTOP || ord_typ == OP_SELLLIMIT || ord_typ == OP_SELL)
     {
      if(ATR_Daily_Restriction_TimeFrame == PERIOD_D1)
        {
         int i = 0;
         double last_cand_lo = iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
         double threshhold_price = NormalizeDouble(last_cand_lo - ((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100)*last_cand_lo,digits);
         if(iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i)<threshhold_price)
           {
            return false;
           }
        }
      else
        {
         for(int i = iBarShift(_Symbol,ATR_Daily_Restriction_TimeFrame,iTime(_Symbol,PERIOD_D1,0)) ; i>0; i--)
           {
            double last_cand_lo = iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
            double threshhold_price = NormalizeDouble(last_cand_lo - ((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100)*last_cand_lo,digits);
            if(iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i)<threshhold_price)
              {
               return false;
              }
           }
        }
     }

   if(ATR_Daily_Restriction_TimeFrame == PERIOD_D1)
     {
      int i = 0;
      double last_cand_lo = iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
      double last_cand_hi = iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
      if((last_cand_hi-last_cand_lo)>((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100))
        {
         return false;
        }
     }
   else
     {
      for(int i = iBarShift(_Symbol,ATR_Daily_Restriction_TimeFrame,iTime(_Symbol,PERIOD_D1,0)) ; i>0; i--)
        {
         double last_cand_lo = iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
         double last_cand_hi = iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i+1);
         if((last_cand_hi-last_cand_lo)>((ATR_Daily_Rest[i+1]*ATR_Daily_Restriction_Multiplier)/100))
           {
            return false;
           }
        }
     }

   return true;
  }





//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Bull(int i)
  {
   return(iClose(_Symbol,_Period,i)>iOpen(_Symbol,_Period,i));
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Bear(int i)
  {
   return(iClose(_Symbol,_Period,i)<iOpen(_Symbol,_Period,i));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Draw_Rng_Box(double &Range_Hi, double &Range_Lo)
  {
//Print("  Draw_Rng_Box   ");
   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
   ObjectDelete(0,"Rng_Box");
   double hi = 0;
   double lo = 0;

   if(Prior_Candles == High_Low)
     {
      hi = iHigh(_Symbol,Default_Candle_TimeFrame,1);
      lo = iLow(_Symbol,Default_Candle_TimeFrame,1);
      for(int i = 2; i<=Number_Of_Prior_Candles_To_Check; i++)
        {
         hi  = hi + iHigh(_Symbol,Default_Candle_TimeFrame,i);
         lo = lo  + iLow(_Symbol,Default_Candle_TimeFrame,i);
        }

      hi = hi/Number_Of_Prior_Candles_To_Check;
      lo = lo/Number_Of_Prior_Candles_To_Check;
     }
   if(Prior_Candles == Open_Close)
     {
      hi = MathMax(iOpen(_Symbol,Default_Candle_TimeFrame,1),iClose(_Symbol,Default_Candle_TimeFrame,1));
      lo = MathMin(iOpen(_Symbol,Default_Candle_TimeFrame,1),iClose(_Symbol,Default_Candle_TimeFrame,1));
      for(int i = 2; i<=Number_Of_Prior_Candles_To_Check; i++)
        {
         hi  = hi + MathMax(iOpen(_Symbol,Default_Candle_TimeFrame,i),iClose(_Symbol,Default_Candle_TimeFrame,i));
         lo = lo  + MathMin(iOpen(_Symbol,Default_Candle_TimeFrame,i),iClose(_Symbol,Default_Candle_TimeFrame,i));
        }
      hi = hi/Number_Of_Prior_Candles_To_Check;
      lo = lo/Number_Of_Prior_Candles_To_Check;
     }



   double Max_Perc = Price_Buffer_Percentage;

   double Percentage_Of_Price_hi = (Max_Perc/100)*hi;
   double Percentage_Of_Price_lo = (Max_Perc/100)*lo;


   Range_Hi = NormalizeDouble(hi +  Percentage_Of_Price_hi,digits);
   Range_Lo = NormalizeDouble(lo -  Percentage_Of_Price_lo,digits);


   datetime st_time = iTime(_Symbol,Default_Candle_TimeFrame,Number_Of_Prior_Candles_To_Check);

// Print(iTime(_Symbol,Default_Candle_TimeFrame,0));
   datetime en_time = iTime(_Symbol,Default_Candle_TimeFrame,0) + (PeriodSeconds(Default_Candle_TimeFrame)*BreakOut_Validity_Candles) - 1;
   RectangleCreate("Rng_Box",st_time,Range_Lo,en_time,Range_Hi,clrGoldenrod);

  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool RectangleCreate(const string name,datetime time1,double price1,datetime time2,double price2,const color clr)
  {
   const long            chart_ID=0;
   const int             sub_window=0;
   const ENUM_LINE_STYLE style=STYLE_DOT;
   const int             width=1;
   const bool            fill=false;
   const bool            back=true;
   const bool            selection=false;
   const bool            hidden=true;
   const long            z_order=0;
   ObjectDelete(chart_ID,name);
   ObjectCreate(chart_ID,name,OBJ_RECTANGLE,sub_window,time1,price1,time2,price2);
   ObjectSetInteger(chart_ID,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(chart_ID,name,OBJPROP_STYLE,style);
   ObjectSetInteger(chart_ID,name,OBJPROP_WIDTH,width);
   ObjectSetInteger(chart_ID,name,OBJPROP_FILL,fill);
   ObjectSetInteger(chart_ID,name,OBJPROP_BACK,back);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTABLE,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTED,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_HIDDEN,hidden);
   ObjectSetInteger(chart_ID,name,OBJPROP_ZORDER,z_order);
   return(true);
  }





//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Close_Not_Fullfilled_Pending()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == _Symbol && (OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT) && (OrderMagicNumber()==Magic_1 || OrderMagicNumber()==Magic_2 || OrderMagicNumber()==Magic_3))
           {
            if(iBarShift(_Symbol,_Period,OrderOpenTime()) > 0)
              {
               if(OrderDelete(OrderTicket(),clrNONE))
                 {
                  Print(" --------- Deleting Not Fullfilled Pending ----------");
                 }
              }
           }
        }
     }
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Close_Pending_ALL()
  {
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == _Symbol && (OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT) && (OrderMagicNumber()==Magic_1 || OrderMagicNumber()==Magic_2 || OrderMagicNumber()==Magic_3))
           {
            //if(iBarShift(_Symbol,_Period,OrderOpenTime()) > 0)
              {
               if(OrderDelete(OrderTicket(),clrNONE))
                 {
                  //Print(" --------- Deleting Not Fullfilled Pending ----------");
                 }
              }
           }
        }
     }
  }













//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool WReset()
  {
   return(WeekdayFilter(wreset_day));
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool WeekdayFilter(ENUM_DAY_OF_WEEK day)
  {
   MqlDateTime date;
   TimeToStruct(TimeCurrent(), date);
   bool ret = false;
   int cday = date.day_of_week;

   if(cday>(int)day)
      return(true);
   if(cday==(int)day)
      return(IsTimeWithinLimits(wreset_start_hour, wreset_start_minute, 23, 59));

   return(false);
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void UpdateBuffers()
  {
   CopyBuffer(st1_h, 0, 0, 5, st1);
   CopyBuffer(st2_h, 0, 0, 5, st2);
   CopyBuffer(st3_h, 0, 0, 5, st3);
   CopyBuffer(atrpct_h, 0, 0, 5, atrpct);

  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CheckMA(bool &allow_buy, bool &allow_sell)
  {
   bool buy_1 = true;
   bool sell_1 = true;
   if(use_basema1)
     {
      CopyBuffer(ma1_h, 0, 0, 5, ma1);
      if(iClose(NULL,basema1_tf,1) < ma1[1])
        {
         buy_1 = basema1_reverse;
         sell_1 = !buy_1;
        }
      else
        {
         buy_1 = !basema1_reverse;
         sell_1 = !buy_1;
        }
     }

   bool buy_2 = true;
   bool sell_2 = true;
   if(use_basema2)
     {
      CopyBuffer(ma2_h, 2, 0, 5, ma2);
      if(iClose(NULL,basema2_tf,1) < ma2[1])
        {
         buy_2 = basema2_reverse;
         sell_2 = !buy_2;
        }
      else
        {
         buy_2 = !basema2_reverse;
         sell_2 = !buy_2;
        }
     }



   bool buy_5 = true;
   bool sell_5 = true;
   if(use_basema5)
     {
      CopyBuffer(ma5_h, 2, 0, 5, ma5);
      if(iClose(NULL,basema5_tf,1) < ma5[1])
        {
         buy_5 = basema5_reverse;
         sell_5 = !buy_5;
        }
      else
        {
         buy_5 = !basema5_reverse;
         sell_5 = !buy_5;
        }
     }

   bool buy_3 = true;
   bool sell_3 = true;
   if(use_basema3)
     {
      CopyBuffer(ma3_h, 0, 0, 5, ma3);
      if(iClose(NULL,basema3_tf,1) < ma3[1])
        {
         buy_3 = basema3_reverse;
         sell_3 = !buy_3;
        }
      else
        {
         buy_3 = !basema3_reverse;
         sell_3 = !buy_3;
        }
     }

   bool buy_4 = true;
   bool sell_4 = true;
   if(use_basema4)
     {
      CopyBuffer(ma4_h, 0, 0, 5, ma4);
      if(iClose(NULL,basema4_tf,1) < ma4[1])
        {
         buy_4 = basema4_reverse;
         sell_4 = !buy_4;
        }
      else
        {
         buy_4 = !basema4_reverse;
         sell_4 = !buy_4;
        }
     }

   allow_buy = buy_1 && buy_2 && buy_3 && buy_4 && buy_5;
   allow_sell = sell_1 && sell_2 && sell_3 && sell_4&& sell_5;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Comp_Buy()
{
  if(!Enable_Comparison_Master) return true;
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  string str_mandatory = "";
  string str_optional = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  int cnt_mandatory = 0;
  int cnt_optional = 0;  
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  bool ma_chck  = true;  
  bool st_chck  = true;
  bool rsi1_chck  = true;
  bool rsi2_chck  = true;
  bool adx1_chck  = true;
  bool adx2_chck  = true; 
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  
  string ma_str  = "";  
  string st_str  = "";
  string rsi1_str  = "";
  string rsi2_str  = "";
  string adx1_str  = "";
  string adx2_str  = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_ma)
     {
         ma_chck = false;
         CopyBuffer(comp_ma_h, 0, 0, 5, comp_ma);
         if((comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) < comp_ma[1]) ||  (!comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) > comp_ma[1]))
           {
              ma_chck = true;
              ma_str = ma_str+" Passed ";
              if(comp_ma_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+ma_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+ma_str;
               cnt_optional++;
              }             
           }
      if(comp_ma_Mandatory &&  !ma_chck)return false;
     }
     else
     {
        ma_str = ma_str+" Skipped (Disabled) ";
        if(comp_ma_Mandatory)str_mandatory = str_mandatory+"\n"+ma_str;
        else str_optional = str_optional+"\n"+ma_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_st)
     {
      st_chck = false;
      CopyBuffer(comp_st_h, 0, 0, 5, comp_st);
      if((comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) < comp_st[1]) || (!comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) > comp_st[1]))
        {
              st_chck = true;
              st_str = st_str+" Passed ";
              if(comp_st_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+st_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+st_str;
               cnt_optional++;
              }  
        }
      if(comp_st_Mandatory &&  !st_chck)return false;
     }
     else
     {
        st_str = st_str+" Skipped (Disabled) ";
        if(comp_st_Mandatory)str_mandatory = str_mandatory+"\n"+st_str;
        else str_optional = str_optional+"\n"+st_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_rsi_1)
     {
      rsi1_chck = false;
      CopyBuffer(comp_rsi_h_1, 0, 0, 5, comp_rsi_1);
      if(!(comp_rsi_1[1]<RSI_Comp_Minimum_Level_1 || comp_rsi_1[1]>RSI_Comp_Maximum_Level_1))
        {
              rsi1_chck = true;
              rsi1_str = rsi1_str+" Passed ";
              if(comp_rsi_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+rsi1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+rsi1_str;
               cnt_optional++;
              }  
        }
      if(comp_rsi_1_Mandatory &&  !rsi1_chck)return false;
     }
     else
     {
        rsi1_str = rsi1_str+" Skipped (Disabled) ";
        if(comp_rsi_1_Mandatory)str_mandatory = str_mandatory+"\n"+rsi1_str;
        else str_optional = str_optional+"\n"+rsi1_str;
     }          
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_rsi_2)
     {
      rsi2_chck = false;
      CopyBuffer(comp_rsi_h_2, 0, 0, 5, comp_rsi_2);
      if((comp_rsi_2[1]<RSI_Comp_Minimum_Level_2 || comp_rsi_2[1]>RSI_Comp_Maximum_Level_2))
        {
              rsi2_chck = true;
              rsi2_str = rsi2_str+" Passed ";
              if(comp_rsi_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+rsi2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+rsi2_str;
               cnt_optional++;
              }  
        }
      if(comp_rsi_2_Mandatory &&  !rsi2_chck)return false;
     }
     else
     {
        rsi2_str = rsi2_str+" Skipped (Disabled) ";
        if(comp_rsi_2_Mandatory)str_mandatory = str_mandatory+"\n"+rsi2_str;
        else str_optional = str_optional+"\n"+rsi2_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Comp_Use_ADX_1)
     {
      adx1_chck = false;
      CopyBuffer(Hndl_Comp_ADX_1,0,0,10,Comp_ADX_1);
      if(Comp_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_1,0,0,10,Comp_MA_ADX_1);
         if(!(Comp_MA_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_MA_ADX_1[1]>Comp_ADX_Maximum_Level_1))
           {
              adx1_chck = true;
              adx1_str = adx1_str+" Passed ";
              if(Comp_adx_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx1_str;
               cnt_optional++;
              }  
           }
        }
      else
        {
         if(!(Comp_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_ADX_1[1]>Comp_ADX_Maximum_Level_1))
           {
              adx1_chck = true;
              adx1_str = adx1_str+" Passed ";
              if(Comp_adx_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx1_str;
               cnt_optional++;
              }  
           }
        }
      if(Comp_adx_1_Mandatory &&  !adx1_chck)return false;
     }
     else
     {
        adx1_str = adx1_str+" Skipped (Disabled) ";
        if(Comp_adx_1_Mandatory)str_mandatory = str_mandatory+"\n"+adx1_str;
        else str_optional = str_optional+"\n"+adx1_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Comp_Use_ADX_2)
     {
      adx2_chck = false;
      CopyBuffer(Hndl_Comp_ADX_2,0,0,10,Comp_ADX_2);
      if(Comp_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_2,0,0,10,Comp_MA_ADX_2);
         if(!(Comp_MA_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_MA_ADX_2[1]>Comp_ADX_Maximum_Level_2))
           {
              adx2_chck = true;
              adx2_str = adx2_str+" Passed ";
              if(Comp_adx_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx2_str;
               cnt_optional++;
              }  
           }
        }
      else
        {
         if(!(Comp_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_ADX_2[1]>Comp_ADX_Maximum_Level_2))
           {
              adx2_chck = true;
              adx2_str = adx2_str+" Passed ";
              if(Comp_adx_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx2_str;
               cnt_optional++;
              }  
           }
        }
      if(Comp_adx_2_Mandatory &&  !adx2_chck)return false;
     }
     else
     {
        adx2_str = adx2_str+" Skipped (Disabled) ";
        if(Comp_adx_2_Mandatory)str_mandatory = str_mandatory+"\n"+adx2_str;
        else str_optional = str_optional+"\n"+adx2_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+          

   if(cnt_optional>=Comparison_Optional_Minimum_Pass)
   {
    if(Comparison_Enable_Journal)
    {
       Print("==================== [Comparison Check] - Result  TRUE ====================");
       Print(" Mandatory ");
       Print(str_mandatory);         
       Print(" Optional ");
       Print(str_optional);  
       Print("Final Decision: Passed("+cnt_mandatory+" mandatory "+cnt_optional+" optional passed");
    }
    return true;
   }

   return false;
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Comp_Sell()
{
  if(!Enable_Comparison_Master) return true;
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  string str_mandatory = "";
  string str_optional = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  int cnt_mandatory = 0;
  int cnt_optional = 0;  
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  bool ma_chck  = true;  
  bool st_chck  = true;
  bool rsi1_chck  = true;
  bool rsi2_chck  = true;
  bool adx1_chck  = true;
  bool adx2_chck  = true; 
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  
  string ma_str  = "";  
  string st_str  = "";
  string rsi1_str  = "";
  string rsi2_str  = "";
  string adx1_str  = "";
  string adx2_str  = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_ma)
     {
         ma_chck = false;
         CopyBuffer(comp_ma_h, 0, 0, 5, comp_ma);
         if((comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) > comp_ma[1]) ||  (!comp_ma_reverse && iClose(comp_symbol,comp_ma_tf,1) < comp_ma[1]))
           {
              ma_chck = true;
              ma_str = ma_str+" Passed ";
              if(comp_ma_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+ma_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+ma_str;
               cnt_optional++;
              }             
           }
      if(comp_ma_Mandatory &&  !ma_chck)return false;
     }
     else
     {
        ma_str = ma_str+" Skipped (Disabled) ";
        if(comp_ma_Mandatory)str_mandatory = str_mandatory+"\n"+ma_str;
        else str_optional = str_optional+"\n"+ma_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_st)
     {
      st_chck = false;
      CopyBuffer(comp_st_h, 0, 0, 5, comp_st);
      if((comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) > comp_st[1]) || (!comp_st_reverse && iClose(comp_symbol,comp_st_tf,1) < comp_st[1]))
        {
              st_chck = true;
              st_str = st_str+" Passed ";
              if(comp_st_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+st_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+st_str;
               cnt_optional++;
              }  
        }
      if(comp_st_Mandatory &&  !st_chck)return false;
     }
     else
     {
        st_str = st_str+" Skipped (Disabled) ";
        if(comp_st_Mandatory)str_mandatory = str_mandatory+"\n"+st_str;
        else str_optional = str_optional+"\n"+st_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_rsi_1)
     {
      rsi1_chck = false;
      CopyBuffer(comp_rsi_h_1, 0, 0, 5, comp_rsi_1);
      if(!(comp_rsi_1[1]<RSI_Comp_Minimum_Level_1 || comp_rsi_1[1]>RSI_Comp_Maximum_Level_1))
        {
              rsi1_chck = true;
              rsi1_str = rsi1_str+" Passed ";
              if(comp_rsi_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+rsi1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+rsi1_str;
               cnt_optional++;
              }  
        }
      if(comp_rsi_1_Mandatory &&  !rsi1_chck)return false;
     }
     else
     {
        rsi1_str = rsi1_str+" Skipped (Disabled) ";
        if(comp_rsi_1_Mandatory)str_mandatory = str_mandatory+"\n"+rsi1_str;
        else str_optional = str_optional+"\n"+rsi1_str;
     }          
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Check_comp_rsi_2)
     {
      rsi2_chck = false;
      CopyBuffer(comp_rsi_h_2, 0, 0, 5, comp_rsi_2);
      if((comp_rsi_2[1]<RSI_Comp_Minimum_Level_2 || comp_rsi_2[1]>RSI_Comp_Maximum_Level_2))
        {
              rsi2_chck = true;
              rsi2_str = rsi2_str+" Passed ";
              if(comp_rsi_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+rsi2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+rsi2_str;
               cnt_optional++;
              }  
        }
      if(comp_rsi_2_Mandatory &&  !rsi2_chck)return false;
     }
     else
     {
        rsi2_str = rsi2_str+" Skipped (Disabled) ";
        if(comp_rsi_2_Mandatory)str_mandatory = str_mandatory+"\n"+rsi2_str;
        else str_optional = str_optional+"\n"+rsi2_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Comp_Use_ADX_1)
     {
      adx1_chck = false;
      CopyBuffer(Hndl_Comp_ADX_1,0,0,10,Comp_ADX_1);
      if(Comp_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_1,0,0,10,Comp_MA_ADX_1);
         if(!(Comp_MA_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_MA_ADX_1[1]>Comp_ADX_Maximum_Level_1))
           {
              adx1_chck = true;
              adx1_str = adx1_str+" Passed ";
              if(Comp_adx_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx1_str;
               cnt_optional++;
              }  
           }
        }
      else
        {
         if(!(Comp_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_ADX_1[1]>Comp_ADX_Maximum_Level_1))
           {
              adx1_chck = true;
              adx1_str = adx1_str+" Passed ";
              if(Comp_adx_1_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx1_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx1_str;
               cnt_optional++;
              }  
           }
        }
      if(Comp_adx_1_Mandatory &&  !adx1_chck)return false;
     }
     else
     {
        adx1_str = adx1_str+" Skipped (Disabled) ";
        if(Comp_adx_1_Mandatory)str_mandatory = str_mandatory+"\n"+adx1_str;
        else str_optional = str_optional+"\n"+adx1_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   if(Comp_Use_ADX_2)
     {
      adx2_chck = false;
      CopyBuffer(Hndl_Comp_ADX_2,0,0,10,Comp_ADX_2);
      if(Comp_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_2,0,0,10,Comp_MA_ADX_2);
         if(!(Comp_MA_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_MA_ADX_2[1]>Comp_ADX_Maximum_Level_2))
           {
              adx2_chck = true;
              adx2_str = adx2_str+" Passed ";
              if(Comp_adx_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx2_str;
               cnt_optional++;
              }  
           }
        }
      else
        {
         if(!(Comp_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_ADX_2[1]>Comp_ADX_Maximum_Level_2))
           {
              adx2_chck = true;
              adx2_str = adx2_str+" Passed ";
              if(Comp_adx_2_Mandatory) 
              {
               str_mandatory = str_mandatory+"\n"+adx2_str;
               cnt_mandatory++;
              }        
              else
              {
               str_optional = str_optional+"\n"+adx2_str;
               cnt_optional++;
              }  
           }
        }
      if(Comp_adx_2_Mandatory &&  !adx2_chck)return false;
     }
     else
     {
        adx2_str = adx2_str+" Skipped (Disabled) ";
        if(Comp_adx_2_Mandatory)str_mandatory = str_mandatory+"\n"+adx2_str;
        else str_optional = str_optional+"\n"+adx2_str;
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+          

   if(cnt_optional>=Comparison_Optional_Minimum_Pass)
   {
    if(Comparison_Enable_Journal)
    {
       Print("==================== [Comparison Check] - Result  TRUE ====================");
       Print(" Mandatory ");
       Print(str_mandatory);         
       Print(" Optional ");
       Print(str_optional);  
       Print("Final Decision: Passed("+cnt_mandatory+" mandatory "+cnt_optional+" optional passed");
    }
    return true;
   }

   return false;
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CheckComp(bool &allow_buy, bool &allow_sell)
{}
/*
void CheckComp(bool &allow_buy, bool &allow_sell)
  {
  
  string ma_str  = "";  
  string st_str  = "";
  string rsi1_str  = "";
  string rsi2_str  = "";
  string adx1_str  = "";
  string adx2_str  = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  
   bool buy_1 = true;
   bool sell_1 = true;
   if(Check_comp_ma)
     {
      CopyBuffer(comp_ma_h, 0, 0, 5, comp_ma);
      if(iClose(comp_symbol,comp_ma_tf,1) < comp_ma[1])
        {
         buy_1 = false;
         sell_1 = !buy_1;
         if(comp_ma_reverse)
           {
            buy_1 = true;
            sell_1 = false;
           }
        }
      else
        {
         buy_1 = true;
         sell_1 = !buy_1;
         if(comp_ma_reverse)
           {
            buy_1 = false;
            sell_1 = true;
           }
        }
     }     
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   bool buy_2 = true;
   bool sell_2 = true;
   if(Check_comp_st)
     {
      CopyBuffer(comp_st_h, 0, 0, 5, comp_st);
      if(iClose(comp_symbol,comp_st_tf,1) < comp_st[1])
        {
         buy_2 = false;
         sell_2 = !buy_2;

         if(comp_st_reverse)
           {

            sell_2 = false;
            buy_2  = true;
           }
        }
      else
        {
         buy_2 = true;
         sell_2 = !buy_2;

         if(comp_st_reverse)
           {

            sell_2 = true;
            buy_2  = false;
           }
        }
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   bool buy_3 = true;
   bool sell_3 = true;
   if(Check_comp_rsi_1)
     {
      CopyBuffer(comp_rsi_h_1, 0, 0, 5, comp_rsi_1);
      if(comp_rsi_1[1]<RSI_Comp_Minimum_Level_1 || comp_rsi_1[1]>RSI_Comp_Maximum_Level_1)
        {
         buy_3 = false;
         sell_3 = false;
        }
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
   bool buy_4 = true;
   bool sell_4 = true;
   if(Check_comp_rsi_2)
     {
      CopyBuffer(comp_rsi_h_2, 0, 0, 5, comp_rsi_2);
      if(comp_rsi_2[1]<RSI_Comp_Minimum_Level_2 || comp_rsi_2[1]>RSI_Comp_Maximum_Level_2)
        {
         buy_4 = false;
         sell_4 = false;
        }
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
   bool buy_5 = true;
   bool sell_5 = true;
   if(Comp_Use_ADX_1)
     {
      CopyBuffer(Hndl_Comp_ADX_1,0,0,10,Comp_ADX_1);
      if(Comp_Use_ADX_MA_Smoothing_1)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_1,0,0,10,Comp_MA_ADX_1);
         if(Comp_MA_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_MA_ADX_1[1]>Comp_ADX_Maximum_Level_1)
           {
            buy_5 = false;
            sell_5 = false;
           }
        }
      else
        {
         if(Comp_ADX_1[1]<Comp_ADX_Minimum_Level_1 || Comp_ADX_1[1]>Comp_ADX_Maximum_Level_1)
           {
            buy_5 = false;
            sell_5 = false;
           }
        }
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
   bool buy_6 = true;
   bool sell_6 = true;
   if(Comp_Use_ADX_2)
     {
      CopyBuffer(Hndl_Comp_ADX_2,0,0,10,Comp_ADX_2);
      if(Comp_Use_ADX_MA_Smoothing_2)
        {
         CopyBuffer(Comp_Hndl_MA_ADX_2,0,0,10,Comp_MA_ADX_2);
         if(Comp_MA_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_MA_ADX_2[1]>Comp_ADX_Maximum_Level_2)
           {
            buy_6 = false;
            sell_6 = false;
           }
        }
      else
        {
         if(Comp_ADX_2[1]<Comp_ADX_Minimum_Level_2 || Comp_ADX_2[1]>Comp_ADX_Maximum_Level_2)
           {
            buy_6 = false;
            sell_6 = false;
           }
        }
     }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   
   
   
   
   
   allow_buy = buy_1 && buy_2 && buy_3 && buy_4 && buy_5 && buy_6;
   
   
   
   
   allow_sell = sell_1 && sell_2 && sell_3 && sell_4 && sell_5 && sell_6;
  }
*/
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void DeleteOldPendingOrders(int candlesCount, long magicNumber, string symbol)
  {
   datetime cutoffTime = iTime(symbol, PERIOD_CURRENT, candlesCount);

   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tck = OrderGetTicket(i);
      if(OrderSelect(tck))
        {
         if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT ||
            OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
           {

            if(OrderGetString(ORDER_SYMBOL) == symbol)
              {
               if(OrderGetInteger(ORDER_TIME_SETUP) < cutoffTime)
                 {
                  Trade.OrderDelete(OrderGetInteger(ORDER_TICKET));
                 }
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void DeleteLimits(string symbol)
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tck = OrderGetTicket(i);
      if(OrderSelect(tck))
        {
         if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT)
           {
            if(OrderGetString(ORDER_SYMBOL) == symbol)
              {
               Trade.OrderDelete(OrderGetInteger(ORDER_TICKET));
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void DeleteStops(string symbol)
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tck = OrderGetTicket(i);
      if(OrderSelect(tck))
        {
         if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP || OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
           {
            if(OrderGetString(ORDER_SYMBOL) == symbol)
              {
               Trade.OrderDelete(OrderGetInteger(ORDER_TICKET));
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void DrawLine(double price, color clr, int dir)
  {
   string oname = "rangeea_"+(string)iTime(NULL,0,0)+("_TP");
   ObjectCreate(0, oname, OBJ_TREND, 0, 0, 0);
   ObjectSetDouble(0, oname, OBJPROP_PRICE, 0, price);
   ObjectSetDouble(0, oname, OBJPROP_PRICE, 1, price);
   ObjectSetInteger(0, oname, OBJPROP_TIME, 0, iTime(NULL, 0, 1));
   ObjectSetInteger(0, oname, OBJPROP_TIME, 1, iTime(NULL, 0, 0)+PeriodSeconds()*1);
   ObjectSetInteger(0, oname, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, oname, OBJPROP_RAY, false);
   ObjectSetInteger(0, oname, OBJPROP_WIDTH, 1);
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Calculate_Single_RiskPercentage(double Entry,double SL,double Percent)
  {
// double AccountBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   Print("=============== Dynamic Lot Calculation ==============");
   double AmountToRisk =Percent;
   Print("  Amount To Risk ",AmountToRisk);
   double ValuePp = SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   Print("   Symbol Trade Tick Value ",ValuePp);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
   Print("  Smbol Point Value  ",point);
   double Difference = (double(Entry - SL))/point;
   if(Difference < 0)
      Difference *= -1;
      
   Print("  Entry ",Entry,"  SL  ",SL,"   SL Point ",Difference);   
   Difference = Difference*ValuePp;
   
   Print(" Difference*ValuePp  ",Difference);
   
   double val= (AmountToRisk/Difference);

    Print(" (AmountToRisk/Difference)  ",(AmountToRisk/Difference));

   if(_Symbol == "NDX100")
     {
      Print("   Symbol is NDX so Divided by 10 ");
      val = val/10;
      
     }
    Print("  Final Lot Risk  ",val); 
   return val;

  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Get_Buy_Dynamic_SL(double open_price)
  {
   if(Use_Structure_SL_Filter)
     {
         int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
         double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
         Print("============== Structure SL Calculation ==============");
         Print("Entry Price: "+DoubleToString(open_price,digits));
         double min_sl = open_price*(1-(min_atrpct_1/100));
         double max_sl = open_price*(1-(max_atrpct_1/100));
         Print("Min SL %: "+min_atrpct_1+" ➝ Min SL Level "+min_sl);
         Print("Max SL %: "+max_atrpct_1+" ➝ Max SL Level "+max_sl);
         Print("Buffer: "+SL_Structure_Buffer_Percent+"%");
         string s = "";
         for(int i= ArraySize(TFs_List)-1 ;i>=0;i--)
         {
          if(TFs_List[i]>=Structure_Candle_TF_From && TFs_List[i]<=Structure_Candle_TF_To)
          {
           string a = EnumToString(TFs_List[i]);StringReplace(a,"PERIOD_","");
           s = s+a+",";
          }
         }
         Print("Checking TFs: "+s);
         double Valid_SLs[];
         for(int i= ArraySize(TFs_List)-1 ;i>=0;i--)
         {
          if(TFs_List[i]>=Structure_Candle_TF_From && TFs_List[i]<=Structure_Candle_TF_To)
          {
           string a = EnumToString(TFs_List[i]);StringReplace(a,"PERIOD_","");
           Print("---["+a+"]---");
           for(int k = 1; k<=SL_Candle_Count; k++)
           {
            double lo = iLow(_Symbol,TFs_List[i],k);
            double lo_buffered = NormalizeDouble(iLow(_Symbol,TFs_List[i],k)*(1-(SL_Structure_Buffer_Percent/100)),digits);
            bool status = false;
            string status_txt = "";
            if(lo_buffered>min_sl)
            {
             status = false;
             status_txt = "Break Min SL";
            }
            else if(lo_buffered<max_sl)
            {
             status = false;
             status_txt = "Break Max SL";
            }
            else
            {
             status = true;
             status_txt = "Valid";
             ArrayResize(Valid_SLs,ArraySize(Valid_SLs)+1);Valid_SLs[ArraySize(Valid_SLs)-1] = lo_buffered;
            }
            Print("Candle Low: "+DoubleToString(lo,digits)+" → SL (buffered) = "+DoubleToString(iLow(_Symbol,TFs_List[i],k),digits)+" x "+(1-(SL_Structure_Buffer_Percent/100))+" = "+DoubleToString(lo_buffered,digits)+" Min SL: "+DoubleToString(min_sl,digits)+" Max SL "+DoubleToString(max_sl,digits)+" "+(status?"✅":"❎")+" "+status_txt);
           }
          }
         }   
         if(ArraySize(Valid_SLs)>0)
         {
          Print("-- Valid SL Candidates (after buffer + range check) ---");
          for(int i = 0; i<ArraySize(Valid_SLs);i++)
          {
           Print("--> "+Valid_SLs[i]);
          }
          return (Valid_SLs[ArrayMinimum(Valid_SLs,0,WHOLE_ARRAY)]);
         }
         else
         {
          return min_sl;
         }
     }    
     return -1;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double Get_Sell_Dynamic_SL(double open_price)
  {
   if(Use_Structure_SL_Filter)
     {
         int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
         double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
         Print("============== Structure SL Calculation ==============");
         Print("Entry Price: "+DoubleToString(open_price,digits));
         double min_sl = open_price*(1+(min_atrpct_1/100));
         double max_sl = open_price*(1+(max_atrpct_1/100));
         Print("Min SL %: "+min_atrpct_1+" ➝ Min SL Level "+min_sl);
         Print("Max SL %: "+max_atrpct_1+" ➝ Max SL Level "+max_sl);
         Print("Buffer: "+SL_Structure_Buffer_Percent+"%");
         string s = "";
         for(int i= ArraySize(TFs_List)-1 ;i>=0;i--)
         {
          if(TFs_List[i]>=Structure_Candle_TF_From && TFs_List[i]<=Structure_Candle_TF_To)
          {
           string a = EnumToString(TFs_List[i]);StringReplace(a,"PERIOD_","");
           s = s+a+",";
          }
         }
         Print("Checking TFs: "+s);
         double Valid_SLs[];
         for(int i= ArraySize(TFs_List)-1 ;i>=0;i--)
         {
          if(TFs_List[i]>=Structure_Candle_TF_From && TFs_List[i]<=Structure_Candle_TF_To)
          {
           string a = EnumToString(TFs_List[i]);StringReplace(a,"PERIOD_","");
           Print("---["+a+"]---");
           for(int k = 1; k<=SL_Candle_Count; k++)
           {
            double hi = iHigh(_Symbol,TFs_List[i],k);
            double hi_buffered = NormalizeDouble(iHigh(_Symbol,TFs_List[i],k)*(1+(SL_Structure_Buffer_Percent/100)),digits);
            bool status = false;
            string status_txt = "";
            if(hi_buffered<min_sl)
            {
             status = false;
             status_txt = "Break Min SL";
            }
            else if(hi_buffered>max_sl)
            {
             status = false;
             status_txt = "Break Max SL";
            }
            else
            {
             status = true;
             status_txt = "Valid";
             ArrayResize(Valid_SLs,ArraySize(Valid_SLs)+1);Valid_SLs[ArraySize(Valid_SLs)-1] = hi_buffered;
            }
            Print("Candle High: "+DoubleToString(hi,digits)+" → SL (buffered) = "+DoubleToString(hi,digits)+" x "+(1+(SL_Structure_Buffer_Percent/100))+" = "+DoubleToString(hi_buffered,digits)+" Min SL: "+DoubleToString(min_sl,digits)+" Max SL "+DoubleToString(max_sl,digits)+" "+(status?"✅":"❎")+" "+status_txt);
           }
          }
         }   
         if(ArraySize(Valid_SLs)>0)
         {
          Print("-- Valid SL Candidates (after buffer + range check) ---");
          for(int i = 0; i<ArraySize(Valid_SLs);i++)
          {
           Print("--> "+Valid_SLs[i]);
          }
          return (Valid_SLs[ArrayMaximum(Valid_SLs,0,WHOLE_ARRAY)]);
         }
         else
         {
          return max_sl;
         }
     }    
     return -1;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void PrintLog()
  {
   if(!Enable_Range_Journal)
     {
      return;
     }
   if(Is_In_Compreesion())
     {
      Print(" RangeModulation Compression Mode ");
      Print("  Risked Money ",Risked_Money_Multiplier_Compression*trade_risk_money);
      Print(" | TP ",TP_Multiplier_Compression," |  ATR% ",ATR_Percentage_Override_Multiplier_Compression);
      Print(" BB SL ",BB_Trailing_Min_SL_Multiplier_Compression," | RSI SL ",RSI_Trailing_Min_SL_Multiplier_Compression," | Structure SL ",Structure_SL_Multiplier_Compression);
     }
   if(Is_In_Expansion())
     {
      Print(" RangeModulation Expansion Mode ");
      Print("  Risked Money ",Risked_Money_Multiplier_Expansion*trade_risk_money);
      Print(" | TP ",TP_Multiplier_Expansion," |  ATR% ",ATR_Percentage_Override_Multiplier_Expansion);
      Print(" BB SL ",BB_Trailing_Min_SL_Multiplier_Expansion," | RSI SL ",RSI_Trailing_Min_SL_Multiplier_Expansion," | Structure SL ",Structure_SL_Multiplier_Expansion);
     }
   if(Is_In_Mixed_C2In_C1Out())
     {
      Print(" RangeModulation Mixed C2 Inside C1 Outside ");
      Print("  Risked Money ",Risked_Money_Multiplier_Mixed_C2_In_C1_Out*trade_risk_money);
      Print(" | TP ",TP_Multiplier_Mixed_C2_In_C1_Out," |  ATR% ",ATR_Percentage_Override_Multiplier_Mixed_C2_In_C1_Out);
      Print(" BB SL ",BB_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out," | RSI SL ",RSI_Trailing_Min_SL_Multiplier_Mixed_C2_In_C1_Out," | Structure SL ",Structure_SL_Multiplier_Mixed_C2_In_C1_Out);
     }
   if(Is_In_Mixed_C2Out_C1In())
     {
      Print(" RangeModulation Mixed C2 Outside C1 Inside");
      Print("  Risked Money ",Risked_Money_Multiplier_Mixed_C2_Out_C1_In*trade_risk_money);
      Print(" | TP ",TP_Multiplier_Mixed_C2_Out_C1_In," |  ATR% ",ATR_Percentage_Override_Multiplier_Mixed_C2_Out_C1_In);
      Print(" BB SL ",BB_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In," | RSI SL ",RSI_Trailing_Min_SL_Multiplier_Mixed_C2_Out_C1_In," | Structure SL ",Structure_SL_Multiplier_Mixed_C2_Out_C1_In);
     }
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void MakeBuy(string type, double price)
  {
  
  
  
   if(!Check_Commander(_Symbol))
   {
    Print("   ☷☷☷☷☷☷☷☷☷☷☷ Commander Status False   ☷☷☷☷☷☷☷☷☷☷☷☷");
    return;
   }
   if(!checkSpread())
     {
      return;
     }
   if(!check_monday_fiter())
     {
      Print("☷☷☷☷☷☷☷☷☷☷☷ Can Not Place Due To Monday Filter  ☷☷☷☷☷☷☷☷☷☷☷");
      return;
     }
   if(!Check_Consec_Streak())
     {
      Print("☷☷☷☷☷☷☷☷☷☷☷ Can Not Place Due To Consectuive Streak ☷☷☷☷☷☷☷☷☷☷☷");
      return;
     }

   if(Enable_Higher_TF_ATR_Filter)
     {
      CopyBuffer(Hndl_ATR_Filter_HTF,0,0,10,ATR_Filter_HTF);
      if(NormalizeDouble(ATR_Filter_HTF[1],2)<Higher_TF_Min_ATR_Percent || NormalizeDouble(ATR_Filter_HTF[1],2)>Higher_TF_Max_ATR_Percent)
        {
         Print("☷☷☷☷☷☷☷☷☷☷☷    Can Not Place Buy Trade Reason ATR Out Of Range On HTF ",NormalizeDouble(ATR_Filter_HTF[1],2)+" ☷☷☷☷☷☷☷☷☷☷☷");
         return;
        }
     }

   int digits =  SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   if(Enable_Trading_Regime_1)
     {
      if(!Use_Primary_ATR || (NormalizeDouble(atrpct[1],2)>Minimum_ATR_Percentage && NormalizeDouble(atrpct[1],2)<Maximum_ATR_Percentage))
        {

        }
      else
        {
         Print("  Can Not Place Buy :");
         Print(" -----   Reason ------");
         Print("  ATR Perc  ",NormalizeDouble(atrpct[1],2)," is not between ",Minimum_ATR_Percentage," and ",Maximum_ATR_Percentage);
         return;
        }
     }



   if(!Check_Simultenous_Trade())
     {
      return;
     }


    

    check_news();
    if(standard_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Standard Red News ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }
    
    if(special_fomc_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Special FOMC ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }
    
    if(speacial_nfp_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Special NFP ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }    



   double v_min_atrpct = 0;
   double v_tpmult = 0;
   double v_riskmoney = 0;
   string v_comment = "ST ";
   bool v_usetrail = false;

   Trade.SetExpertMagicNumber(Magic_1);
//if(select == 1)
     {
      v_tpmult = tp_mult_1;
      Get_TP_Mult(v_tpmult);
      v_riskmoney = trade_risk_money;
      double risk_money_mult = 1;
      Get_Risk_Money_Mult(risk_money_mult);
      v_riskmoney = risk_money_mult*v_riskmoney;
      v_usetrail = Use_Post_Trailing;
     }


   double openprice = NormalizeDouble(price, _Digits);
   if(type == "limit")
     {
      openprice = MathMin(Ask-SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point, openprice);

     }
   else
     {
      if(openprice<(Ask+SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point))
        {
         openprice = Ask+SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point;
        }

     }

   double sl_level = 0;
   if(Use_Structure_SL_Filter)
     {
      sl_level = NormalizeDouble(Get_Buy_Dynamic_SL(openprice),_Digits);
     }
   else
     {
      sl_level = NormalizeDouble(openprice - ((min_atrpct_1/100)*openprice),digits);
      ObjectSetString(0,dashboard_prefix+"Lab5",OBJPROP_TEXT,"[SL Logic]: "+"SL  @  Min SL "+DoubleToString(sl_level,digits));
     }
   double sl_points = MathAbs(NormalizeDouble(openprice - sl_level,digits)/point);
   double tp_level = NormalizeDouble(openprice+(v_tpmult*sl_points)*point, digits);









   double lotA = AlignLots(fixlot);
   if(use_dynamic_lots && sl_level>0  && sl_points>0)
     {

      lotA = NormalizeDouble(Calculate_Single_RiskPercentage(openprice,sl_level,v_riskmoney),2);

      lotA=AlignLots(lotA);
      Print("Sl Points calculated are "+sl_points + "  "+lotA);
     }


   DrawLine(tp_level, clrRed, 1);

   v_comment = NormalizeDouble(sl_points,_Digits);

   if(!Check_Price_Range_Broker(OP_BUY,openprice))     
   {
    return;
   }
   if(checkBuyThresRSI())
     {
      if(lotA>MaxCapLotSize)
      {
       lotA = MaxCapLotSize;
       Print(" Lot Size is capped to "+MaxCapLotSize+"  Due to Abnormal Calculation ");
       lotA=AlignLots(lotA);
       Print(" Final Lot "+lotA);
      }
      if(type == "limit")
        {
         if(Trade.BuyLimit(lotA, openprice, NULL, sl_level, v_usetrail?0:tp_level, ORDER_TIME_GTC, 0, v_comment))
           {
            // ExpertRemove();
            PrintLog();
           }
        }
      else
        {
         if(Trade.BuyStop(lotA,openprice, NULL, sl_level, v_usetrail?0:tp_level, ORDER_TIME_GTC, 0, v_comment))
           {
            //ExpertRemove();
            PrintLog();
           }

        }
     }

   int sz = ArrayRange(tp_levels,0);
   ArrayResize(tp_levels, sz+1);
   tp_levels[sz].tck = Trade.ResultOrder();
   tp_levels[sz].tp_level = tp_level;
   tp_levels[sz].pclosed = false;
   tp_levels[sz].sl_level = sl_level;
   tp_levels[sz].open_level = price;
   
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void MakeSell(string type, double price)
  {
  if(!Check_Commander(_Symbol))
   {
    Print("   ☷☷☷☷☷☷☷☷☷☷☷ Commander Status False   ☷☷☷☷☷☷☷☷☷☷☷☷");
    return;
   }
   if(!checkSpread())
     {
      return;
     }
   if(!check_monday_fiter())
     {
      Print(" Can Not Place Due To Monday Filter  ");
      return;
     }
   if(!Check_Consec_Streak())
     {
      Print(" Can Not Place Due To Consectuive Streak ");
      return;
     }
   if(Enable_Higher_TF_ATR_Filter)
     {
      CopyBuffer(Hndl_ATR_Filter_HTF,0,0,10,ATR_Filter_HTF);
      if(NormalizeDouble(ATR_Filter_HTF[1],2)<Higher_TF_Min_ATR_Percent || NormalizeDouble(ATR_Filter_HTF[1],2)>Higher_TF_Max_ATR_Percent)
        {
         Print("    Can Not Place Sell Trade Reason ATR Out Of Range On HTF ",NormalizeDouble(ATR_Filter_HTF[1],2));
         return;
        }
     }

   int digits =  SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(_Symbol,SYMBOL_POINT);

   if(Enable_Trading_Regime_1)
     {
      if(!Use_Primary_ATR || (NormalizeDouble(atrpct[1],2)>Minimum_ATR_Percentage && NormalizeDouble(atrpct[1],2)<Maximum_ATR_Percentage))
        {

        }
      else
        {
         Print("  Can Not Place Buy :");
         Print(" -----   Reason ------");
         Print("  ATR Perc  ",NormalizeDouble(atrpct[1],2)," is not between ",Minimum_ATR_Percentage," and ",Maximum_ATR_Percentage);
         return;
        }
     }

   if(!Check_Simultenous_Trade())
     {
      return;
     }
    //check_news();
    if(standard_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Standard Red News ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }
    
    if(special_fomc_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Special FOMC ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }
    
    if(speacial_nfp_red_news)
    {
     Print("☷☷☷☷☷☷☷☷☷☷☷ News Block Due To Special NFP ☷☷☷☷☷☷☷☷☷☷☷");
     return;
    }
   //Print("   price ------->  ",price);
   double v_slmult = 0;
   double v_tpmult = 0;
   double v_riskmoney = 0;
   string v_comment = "ST ";
   bool v_usetrail = false;

   Trade.SetExpertMagicNumber(Magic_1);

//if(select == 1)
     {
      v_tpmult = tp_mult_1;
      Get_TP_Mult(v_tpmult);
      v_riskmoney = trade_risk_money; /////* lots_mult_1;
      double risk_money_mult = 1;
      Get_Risk_Money_Mult(risk_money_mult);
      v_riskmoney = risk_money_mult*v_riskmoney;
      v_usetrail = Use_Post_Trailing;
     }


   double openprice = NormalizeDouble(price, _Digits);

   if(type == "limit")
     {
      openprice = MathMin(Bid+SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point, openprice);
     }
   else
     {
      if(openprice>(Bid-SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point))
        {
         openprice = Bid-SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*_Point;
        }


     }
   openprice = NormalizeDouble(price, _Digits);


   double sl_level = 0;
   if(Use_Structure_SL_Filter)
     {
      sl_level = NormalizeDouble(Get_Sell_Dynamic_SL(openprice),_Digits);
     }
   else
     {
      sl_level = NormalizeDouble(openprice + ((max_atrpct_1/100)*openprice),digits);
      ObjectSetString(0,dashboard_prefix+"Lab5",OBJPROP_TEXT,"[SL Logic]: "+"SL  @  Max SL "+DoubleToString(sl_level,digits));
     }
     
   double sl_points = MathAbs(NormalizeDouble(openprice - sl_level,digits)/point);
   double tp_level = NormalizeDouble(openprice-(v_tpmult*sl_points)*point, digits);




   double lotA = AlignLots(fixlot);
   if(use_dynamic_lots && sl_level>0  && sl_points>0)
     {

      lotA = NormalizeDouble(Calculate_Single_RiskPercentage(openprice,sl_level,v_riskmoney),2);

      lotA=AlignLots(lotA);


     }


   DrawLine(tp_level, clrRed, 1);

   v_comment = NormalizeDouble(sl_points,_Digits);
   if(!Check_Price_Range_Broker(OP_SELL,openprice))     
   {
    return;
   }
   if(checkSellThresRSI())
     {
      
      if(lotA>MaxCapLotSize)
      {
       lotA = MaxCapLotSize;
       Print(" Lot Size is capped to "+MaxCapLotSize+"  Due to Abnormal Calculation ");
       lotA=AlignLots(lotA);
       Print(" Final Lot "+lotA);
      }
           
      if(type == "limit")
        {
         if(Trade.SellLimit(lotA, openprice, NULL, sl_level, v_usetrail?0:tp_level, ORDER_TIME_GTC, 0, v_comment))
           {
            //ExpertRemove();
            PrintLog();
           }
        }
      else
        {
         if(Trade.SellStop(lotA, openprice, NULL, sl_level, v_usetrail?0:tp_level, ORDER_TIME_GTC, 0, v_comment))
           {
            //ExpertRemove();
            PrintLog();
           }
        }
     }
   int sz = ArrayRange(tp_levels,0);
   ArrayResize(tp_levels, sz+1);
   tp_levels[sz].tck = Trade.ResultOrder();
   tp_levels[sz].tp_level = tp_level;
   tp_levels[sz].pclosed = false;
   tp_levels[sz].sl_level = sl_level;
   tp_levels[sz].open_level = price;
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
/*
void PostTrailing(ENUM_TIMEFRAMES Trail_TF,double Buffer_Perc,bool buy_trail,bool sell_trail)
  {
   if(Use_Post_Trailing)
     {
      bool Cnd_Conf = false;
      if(Trailing_Post_Candle_Colour == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(Trailing_Post_Candle_Colour == Cand_Green && iClose(_Symbol,Trail_TF,1)>iOpen(_Symbol,Trail_TF,1))
        {
         Cnd_Conf = true;
        }
      if(Trailing_Post_Candle_Colour == Cand_Red && iClose(_Symbol,Trail_TF,1)<iOpen(_Symbol,Trail_TF,1))
        {
         Cnd_Conf = true;
        }
      if(Cnd_Conf)
        {
         for(int i = OrdersTotal()-1 ; i>=0 ; i--)
           {
            if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
              {
               if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol)
                 {
                  string comment = OrderComment();
                  string outputArray[];
                  int arraySize = StringSplit(comment, ',', outputArray);
                  string target_SL_points = comment;
                  if(arraySize > 0)
                    {
                     target_SL_points = outputArray[0];
                    }

                  int sl_points = StringToInteger(target_SL_points);


                  if(OrderType() == OP_BUY && buy_trail)
                    {
                     double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                     double expected_profit = sl_points*tp_mult_1;
                     if(profit >= expected_profit)
                       {
                        double new_sl = NormalizeDouble(iLow(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                        double new_sl_points = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - new_sl,_Digits)/_Point;

                        if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                             {
                              if(Journal_Post_Trailing)
                                {
                                 Print(" Post Trailing ");
                                }
                             }
                          }
                       }
                    }
                  else
                     if(OrderType()==OP_SELL && sell_trail)
                       {
                        double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                        double expected_profit = sl_points*tp_mult_1;
                        if(profit >= expected_profit)
                          {
                           double new_sl = NormalizeDouble(iHigh(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                           double new_sl_points = NormalizeDouble(new_sl - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                           if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                             {
                              if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                                {
                                 if(Journal_Post_Trailing)
                                   {
                                    Print(" Post Trailing ");
                                   }
                                }
                             }
                          }
                       }
                 }

              }
           }
        }
     }
  }
*/  
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

void PostTrailing(ENUM_TIMEFRAMES Trail_TF,double Buffer_Perc,bool buy_trail,bool sell_trail)
  {
   if(Use_Post_Trailing)
     {
      bool Cnd_Conf = false;
      if(Trailing_Post_Candle_Colour == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(Trailing_Post_Candle_Colour == Cand_Green)
        {
         if(Post_Trail_Method == Trigger_On_Close)Cnd_Conf = (iClose(_Symbol,Trail_TF,1)>iOpen(_Symbol,Trail_TF,1)); 
         if(Post_Trail_Method == Trigger_On_Cross)Cnd_Conf = (iClose(_Symbol,Trail_TF,0)>iOpen(_Symbol,Trail_TF,0)); 
        }
      if(Trailing_Post_Candle_Colour == Cand_Red)
        {
           if(Post_Trail_Method == Trigger_On_Close)Cnd_Conf = (iClose(_Symbol,Trail_TF,1)<iOpen(_Symbol,Trail_TF,1)); 
           if(Post_Trail_Method == Trigger_On_Cross)Cnd_Conf = (iClose(_Symbol,Trail_TF,0)<iOpen(_Symbol,Trail_TF,0));           
        }
      if(Cnd_Conf)
        {
         for(int i = OrdersTotal()-1 ; i>=0 ; i--)
           {
            if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
              {
               if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol)
                 {
                  string comment = OrderComment();
                  string outputArray[];
                  int arraySize = StringSplit(comment, ',', outputArray);
                  string target_SL_points = comment;
                  if(arraySize > 0)
                    {
                     target_SL_points = outputArray[0];
                    }

                  int sl_points = StringToInteger(target_SL_points);


                  if(OrderType() == OP_BUY && buy_trail)
                    {
                     double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                     double expected_profit = sl_points*tp_mult_1;
                     if(profit >= expected_profit)
                       {
                        double new_sl = 0;
                        
                        if(Post_Trail_Type == Trail_By_Candle)
                        {
                         new_sl = NormalizeDouble(iLow(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                        }
                        if(Post_Trail_Type == Trail_By_Percent)
                        {
                         new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)*(1-Buffer_Perc/100), _Digits);
                        }
                       
                        if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                             {
                              if(Journal_Post_Trailing)
                                {
                                 Print(" Post Trailing ");
                                 ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+" Post Trailing New SL "+new_sl);
                                
                                }
                             }
                          }
                       }
                    }
                  else
                     if(OrderType()==OP_SELL && sell_trail)
                       {
                        double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                        double expected_profit = sl_points*tp_mult_1;
                        if(profit >= expected_profit)
                          {
                           double new_sl = 0;
                           
                           if(Post_Trail_Type == Trail_By_Candle)
                           {
                            new_sl = NormalizeDouble(iHigh(NULL, Trail_TF, 1)*(1+Buffer_Perc/100), _Digits);
                           }
                           if(Post_Trail_Type == Trail_By_Percent)
                           {
                            new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)*(1+Buffer_Perc/100), _Digits);
                           }
                           
                           
                           if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                             {
                              if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                                {
                                 if(Journal_Post_Trailing)
                                   {
                                    Print(" Post Trailing ");
                                    ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+" Post Trailing New SL "+new_sl);
                                   }
                                }
                             }
                          }
                       }
                 }

              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+


void PostTP_InsideBar_Exit()
  {
   if(!Use_PostTP_InsideBar_Exit)
     {
      return;
     }
   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
   double hi = iHigh(_Symbol,Price_Structure_TF,1);
   double lo = iLow(_Symbol,Price_Structure_TF,1);
   double cls =  iClose(_Symbol,Price_Structure_TF,1);
   double highest = iHigh(_Symbol,Price_Structure_TF,2);
   double lowest = iLow(_Symbol,Price_Structure_TF,2);
   for(int i = 2; i<2+Compression_Candle_Count; i++)
     {
      if(iHigh(_Symbol,Price_Structure_TF,i)>highest)
        {
         highest = iHigh(_Symbol,Price_Structure_TF,i);
        }
      if(iLow(_Symbol,Price_Structure_TF,i)<lowest)
        {
         lowest = iLow(_Symbol,Price_Structure_TF,i);
        }
     }
   highest = NormalizeDouble(highest+((Compression_Buffer_Percentage/100)*highest),digits);
   lowest = NormalizeDouble(lowest-((Compression_Buffer_Percentage/100)*lowest),digits);
   if(cls>=lowest && cls<= highest)
     {
      for(int i = OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol && iBarShift(_Symbol,Price_Structure_TF,OrderOpenTime())>=1)
              {
               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }

               int sl_points = StringToInteger(target_SL_points);
               if(OrderType() == OP_BUY)
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                  double expected_profit = sl_points*tp_mult_1;
                  double expected_profit_prc = NormalizeDouble(OrderOpenPrice()+expected_profit*point,digits);
                  if(profit >= expected_profit && hi>=expected_profit_prc)
                    {
                     if(OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20))
                     {
                      Print("------------------  Close Buy On Inside Bar Post TP ------------------");
                      
                     }
                    }
                 }
               else if(OrderType()==OP_SELL)
                    {
                     double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                     double expected_profit = sl_points*tp_mult_1;
                     double expected_profit_prc = NormalizeDouble(OrderOpenPrice()-expected_profit*point,digits);
                     if(profit >= expected_profit && lo<=expected_profit_prc)
                       {
                        if(OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),20))
                        {
                         Print("------------------  Close Sell On Inside Bar Post TP ------------------");
                       
                        }
                       }
                    }
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
  
void PreTrailing(ENUM_TIMEFRAMES Trail_TF,double Buffer_Perc,bool buy_trail,bool sell_trail)
  {
   if(Use_Pre_Trailing)
     {
      for(int i = OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol)
              {


               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }

               int sl_points = StringToInteger(target_SL_points);

               if(OrderType() == OP_BUY && buy_trail && check_prior_cnds_tp_trail(OP_BUY))
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;

                  double expected_profit = sl_points*Trailing_Pre_tp_mult_1;
                  if(profit>0 && profit >= expected_profit)
                    {
                     double new_sl = NormalizeDouble(iLow(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                     if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                        {
                         ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+" Pre Trailing New SL "+new_sl);
                        }
                       }
                    }
                 }
               else
                  if(OrderType()==OP_SELL && sell_trail && check_prior_cnds_tp_trail(OP_SELL))
                    {
                     double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                     double expected_profit = sl_points*Trailing_Pre_tp_mult_1;
                     if(profit>0 && profit >= expected_profit)
                       {
                        double new_sl = NormalizeDouble(iHigh(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                        if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                           {
                            ObjectSetString(0,dashboard_prefix+"Lab6",OBJPROP_TEXT,"[Trailing Logic]: "+" Pre Trailing New SL "+new_sl);
                           }
                          }
                       }
                    }
              }

           }


        }
     }
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_prior_cnds_tp_trail(int ord_typ)
  {
   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   if(!Check_Prior_Candles_For_Pre_TP_Trailing)
     {
      return true;
     }
   if(ord_typ == OP_BUY)
     {
      double highest = iHigh(_Symbol,TimeFrame_For_Checking,1);
      for(int i = 2; i<=No_Of_Prior_Cands; i++)
        {
         if(iHigh(_Symbol,TimeFrame_For_Checking,i)>highest)
           {
            highest = iHigh(_Symbol,TimeFrame_For_Checking,i);
           }
        }
      double prc = NormalizeDouble(highest + (atrpct[1]/100)*ATR_PERC_Multipler_Buffer*highest,digits);
      if(iClose(_Symbol,TimeFrame_For_Checking,0)>prc)
        {
         return true;
        }
      else
        {
         return false;
        }
     }
   if(ord_typ == OP_SELL)
     {
      double lowest = iLow(_Symbol,TimeFrame_For_Checking,1);
      for(int i = 2; i<=No_Of_Prior_Cands; i++)
        {
         if(iLow(_Symbol,TimeFrame_For_Checking,i)<lowest)
           {
            lowest = iLow(_Symbol,TimeFrame_For_Checking,i);
           }
        }
      double prc = NormalizeDouble(lowest - (atrpct[1]/100)*ATR_PERC_Multipler_Buffer*lowest,digits);
      if(iClose(_Symbol,TimeFrame_For_Checking,0)<prc)
        {
         return true;
        }
      else
        {
         return false;
        }
     }
   return true;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void BreakEven()
  {
   if(Use_BreakEven)
     {
      for(int i = OrdersTotal()-1 ; i>=0 ; i--)
        {
         if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
           {
            if((OrderMagicNumber() == Magic_1 || OrderMagicNumber() == Magic_2 || OrderMagicNumber() == Magic_3) && OrderSymbol() == _Symbol)
              {

               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }

               int sl_points = StringToInteger(target_SL_points);

               if(OrderType() == OP_BUY)
                 {
                  double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                  double expected_profit = sl_points*BE_Trigger_Multiplier;
                  if(profit >= expected_profit)
                    {
                     double new_sl = NormalizeDouble(OrderOpenPrice()+(BE_Offset_Multiplier*sl_points)*_Point, _Digits);
                     if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                        {
                         ObjectSetString(0,dashboard_prefix+"Lab7",OBJPROP_TEXT,"[Breakeven]: New SL @ "+new_sl);
                         //LabelCreate(dashboard_prefix+"Lab7",20,170,"[Breakeven]: 0",10,C'236,233,216',"Segoe UI");
                        }
                       }
                    }
                 }
               else
                  if(OrderType()==OP_SELL)
                    {
                     double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                     double expected_profit = sl_points*BE_Trigger_Multiplier;
                     if(profit>0 && profit >= expected_profit)
                       {
                        double new_sl = NormalizeDouble(OrderOpenPrice()-(BE_Offset_Multiplier*sl_points)*_Point, _Digits);
                        if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                           {
                            ObjectSetString(0,dashboard_prefix+"Lab7",OBJPROP_TEXT,"[Breakeven]: New SL @ "+new_sl);
                           }
                          }
                       }
                    }
              }

           }


        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_trail_override(int ord_typ)
  {
   if(!ATR_Perc_OvreRide_Trail)
     {
      return false;
     }
   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
   int i = 0;
   if(ord_typ == OP_BUYSTOP || ord_typ == OP_BUYLIMIT || ord_typ == OP_BUY)
     {
      double last_cand_hi = iHigh(_Symbol,ATR_Perc_OverRide_TF,i+1);
      double threshhold_price = NormalizeDouble(last_cand_hi+ ((ATR_PERC_OverRide[i+1]*ATR_Perc_OvreRide_MultiPlier)/100)*last_cand_hi,digits);
      if(iHigh(_Symbol,ATR_Daily_Restriction_TimeFrame,i)>threshhold_price)
        {
         return true;
        }
     }
   if(ord_typ == OP_SELLSTOP || ord_typ == OP_SELLLIMIT || ord_typ == OP_SELL)
     {
      double last_cand_lo = iLow(_Symbol,ATR_Perc_OverRide_TF,i+1);
      double threshhold_price = NormalizeDouble(last_cand_lo - ((ATR_PERC_OverRide[i+1]*ATR_Perc_OvreRide_MultiPlier)/100)*last_cand_lo,digits);
      if(iLow(_Symbol,ATR_Daily_Restriction_TimeFrame,i)<threshhold_price)
        {
         return true;
        }
     }
   return false;
  }
datetime tm,tm1;
datetime tm_trail_atr_override;
void ProcessExits()
  {

   if(tm!=iTime(_Symbol,Trailing_Post_TF,1))
     {
      PostTrailing(Trailing_Post_TF,Trailing_Post_Candle_Percentage,true,true);
      tm=iTime(_Symbol,Trailing_Post_TF,1);
     }
   if(tm1!=iTime(_Symbol,Trailing_Pre_TF,1))
     {
      PreTrailing(Trailing_Pre_TF,Trailing_Pre_Buffer_Percentage,true,true);
      tm1=iTime(_Symbol,Trailing_Pre_TF,1);
     }
   if(ATR_Perc_OvreRide_Trail)
     {
      if(tm_trail_atr_override!=iTime(_Symbol,ATR_Perc_OverRide_Trailing_Stop_TF,0))
        {
         CopyBuffer(Hndl_ATR_PERC_OverRide,0,0,10,ATR_PERC_OverRide);
         bool buy_override = check_trail_override(OP_BUY);
         bool sell_override = check_trail_override(OP_SELL);
         PostTrailing(ATR_Perc_OverRide_Trailing_Stop_TF,ATR_Perc_OverRide_Candle_Perc_Post,buy_override,sell_override);
         
         PreTrailing(ATR_Perc_OverRide_Trailing_Stop_TF,ATR_Perc_OverRide_Buffer_Perc_Pre,buy_override,sell_override);

         tm_trail_atr_override = iTime(_Symbol,ATR_Perc_OverRide_Trailing_Stop_TF,0);
        }
     }

    if(Post_Trail_Method == Trigger_On_Cross)
    {
     PostTrailing(Trailing_Post_TF,Trailing_Post_Price_Percentage,true,true);
     if(ATR_Perc_OvreRide_Trail)
     {
        CopyBuffer(Hndl_ATR_PERC_OverRide,0,0,10,ATR_PERC_OverRide);
        bool buy_override = check_trail_override(OP_BUY);
        bool sell_override = check_trail_override(OP_SELL);
        PostTrailing(ATR_Perc_OverRide_Trailing_Stop_TF,ATR_Perc_OverRide_Price_Perc_Post,buy_override,sell_override);       
     }
    }



   BreakEven();
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CheckOrders()
  {
   buy_limits = 0;
   sell_limits = 0;
   buy_stops = 0;
   sell_stops = 0;
   buys = 0;
   sells = 0;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      PositionsInfo.SelectByIndex(i);
      if((PositionsInfo.Magic() == Magic_1 || PositionsInfo.Magic() == Magic_2 || PositionsInfo.Magic() == Magic_3) && PositionsInfo.Symbol() == Symbol())
        {
         if(PositionsInfo.PositionType() == POSITION_TYPE_BUY)
            buys++;
         else
            if(PositionsInfo.PositionType() == POSITION_TYPE_SELL)
               sells++;
        }
     }
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tck = OrderGetTicket(i);
      bool ret = OrderSelect(tck);
      if((OrderGetInteger(ORDER_MAGIC) == Magic_1 || OrderGetInteger(ORDER_MAGIC) == Magic_2 || OrderGetInteger(ORDER_MAGIC) == Magic_3) && OrderGetString(ORDER_SYMBOL) == Symbol())
         if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_LIMIT)
            buy_limits++;
         else
            if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_LIMIT)
               sell_limits++;
            else
               if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_BUY_STOP)
                  buy_stops++;
               else
                  if(OrderGetInteger(ORDER_TYPE) == ORDER_TYPE_SELL_STOP)
                     sell_stops++;
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double AlignLots(double lots, string symbol = "")
  {
   if(symbol == "")
      symbol = Symbol();
   double LotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double MinLots = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double MaxLots = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   lots = MathRound(lots / LotStep) * LotStep;
   if(lots < MinLots)
      lots = MinLots;
   if(lots > MaxLots)
      lots = MaxLots;
   return lots;
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool HoursFilter(string startTime, string endTime, datetime comp)
  {
   string today = TimeToString(iTime(NULL, PERIOD_D1, 0), TIME_DATE);
   datetime start = StringToTime(today + " " + startTime);
   datetime end = StringToTime(today + " " + endTime);
   if(end < start)
      return (comp > start || comp < end);
   else
      return (comp > start && comp < end);
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CloseAll(string type = "any")
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      PositionsInfo.SelectByIndex(i);
      if((PositionsInfo.Magic() == Magic_1 || PositionsInfo.Magic() == Magic_2 || PositionsInfo.Magic() == Magic_3) && PositionsInfo.Symbol() == Symbol())
        {
         if(type == "any" || (type == "buys" && PositionsInfo.PositionType()==POSITION_TYPE_BUY) || (type == "sells" && PositionsInfo.PositionType()==POSITION_TYPE_SELL))
            Trade.PositionClose(PositionsInfo.Ticket());
        }
     }
  }
//+------------------------------------------------------------------+
double GetLots(double riskPercentage, int stopLossPoints, string sym = "")
  {
   if(sym == "")
      sym = Symbol();
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double pointValue = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
   double riskmoney = balance * riskPercentage / 100;

   Print("Amount to risk "+riskmoney);
   double lotSize = riskmoney / (stopLossPoints * pointValue);
   return lotSize;
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsTimeWithinLimits(int hour_start, int minute_start, int hour_end, int minute_end)
  {
   datetime current_time = TimeCurrent();
   MqlDateTime time_struct;
   TimeToStruct(current_time, time_struct);

   int current_hour = time_struct.hour;
   int current_minute = time_struct.min;
   int start_minutes = hour_start * 60 + minute_start;
   int end_minutes = hour_end * 60 + minute_end;
   int current_minutes = current_hour * 60 + current_minute;

   if(start_minutes <= end_minutes)
     {
      return (current_minutes >= start_minutes && current_minutes <= end_minutes);
     }
   else
     {
      return (current_minutes >= start_minutes || current_minutes <= end_minutes);
     }
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool IsWeekday(int weekday)
  {
   MqlDateTime time_struct;
   TimeToStruct(TimeCurrent(), time_struct);
   return (time_struct.day_of_week == weekday);
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CloseAllOrders(string type = "any")
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tck = OrderGetTicket(i);
      if(OrderSelect(tck))
        {
         if(OrderGetString(ORDER_SYMBOL) == Symbol())
           {
            int orderType = (int)OrderGetInteger(ORDER_TYPE);
            if(type == "any" || (type == "buys" && (orderType == ORDER_TYPE_BUY_LIMIT || orderType == ORDER_TYPE_BUY_STOP)) ||
               (type == "sells" && (orderType == ORDER_TYPE_SELL_LIMIT || orderType == ORDER_TYPE_SELL_STOP)))
              {
               Trade.OrderDelete(OrderGetInteger(ORDER_TICKET));
              }
           }
        }
     }
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
bool WithinDailyLimits(double loss_tgt = 0, double profit_tgt = 0, bool closerunners = false)
  {
   double prof = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      PositionsInfo.SelectByIndex(i);
      if(PositionsInfo.Symbol() == Symbol())
        {
         prof += PositionsInfo.Profit() + PositionsInfo.Swap();
         double future_commission = PositionsInfo.Volume()*GetCommissionPerFullLot(PositionsInfo.Ticket());
         prof += future_commission;
        }
     }
   double closed = ClosedProfit(iTime(NULL, PERIOD_D1, 0));

   prof += closed;
   if((profit_tgt > 0 && prof > profit_tgt) || (loss_tgt > 0 && -prof > loss_tgt))
     {
      if(closerunners)
         CloseAll();
      static datetime open = 0;
      if(open != iTime(NULL, PERIOD_D1, 0))
         Print("Daily limit reached!");
      open = iTime(NULL, PERIOD_D1, 0);
      return(false);
     }
   return(true);
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
double ClosedProfit(datetime start_time)
  {
   HistorySelect(start_time, TimeCurrent());
   int total = HistoryDealsTotal();
   double prof = 0;
   for(int i=total-1; i>=0; i--)
     {
      ulong tck = HistoryDealGetTicket(i);
      if(HistoryDealGetString(tck, DEAL_SYMBOL) != Symbol())
         continue;
      if(HistoryDealGetInteger(tck, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;
      prof += HistoryDealGetDouble(tck, DEAL_PROFIT);
      prof += HistoryDealGetDouble(tck, DEAL_COMMISSION);
      prof += HistoryDealGetDouble(tck, DEAL_SWAP);
     }
   return(prof);
  }

//+------------------------------------------------------------------+
double GetCommissionPerFullLot(ulong positionTicket)
  {
   double totalCommission = 0.0;
   double tradeVolume = 0.0;
   HistorySelect(TimeCurrent()-2592000, TimeCurrent());
   int dealsTotal = HistoryDealsTotal();
   for(int i = 0; i < dealsTotal; i++)
     {
      ulong dealTicket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID) == positionTicket)
        {
         if(HistoryDealGetInteger(dealTicket, DEAL_ENTRY) == DEAL_ENTRY_IN)
           {
            double commission = HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
            double volume = HistoryDealGetDouble(dealTicket, DEAL_VOLUME);
            totalCommission += commission;
            tradeVolume += volume;
           }
        }
     }
   if(tradeVolume == 0.0)
     {
      return 0.0;
     }
   double commissionPerFullLot = totalCommission / tradeVolume * 1.0;
   return commissionPerFullLot;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int LossesInRow(datetime start_time)
  {
   HistorySelect(start_time, TimeCurrent());
   int total = HistoryDealsTotal();
   int losses_in_row = 0;

   for(int i=total-1; i>=0; i--)
     {
      ulong tck = HistoryDealGetTicket(i);
      if((HistoryDealGetInteger(tck, DEAL_MAGIC) != Magic_1 && HistoryDealGetInteger(tck, DEAL_MAGIC) != Magic_2 && HistoryDealGetInteger(tck, DEAL_MAGIC) != Magic_3)|| HistoryDealGetString(tck, DEAL_SYMBOL) != Symbol())
         continue;
      if(HistoryDealGetInteger(tck, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;

      double profit = HistoryDealGetDouble(tck, DEAL_PROFIT);
      if(profit < 0)
        {
         losses_in_row++;
        }
      else
        {
         break;
        }
     }
   return losses_in_row;
  }
//+------------------------------------------------------------------+


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool DaysFilter(datetime dt)
  {
   MqlDateTime date;
   TimeToStruct(dt, date);
   bool ret = false;
   int day = date.day_of_week;

   if(day==1)
      return(trade_mon);
   if(day==2)
      return(trade_tue);
   if(day==3)
      return(trade_wed);
   if(day==4)
      return(trade_thu);
   if(day==5)
      return(trade_fri);
   if(day==6)
      return(trade_sat);
   if(day==0)
      return(trade_sun);
   return(false);
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Trade_Fiter(int magic_no)
  {
   if(Allow_Multiple_Trades_On_Same_Candle == false && Allow_Entry_on_Other_Candle_While_This_Trade_is_Open == false && Allow_Only_On_Different_SuperTrend == false)
     {
      if(Tot_TradesAll() > 0)
        {
         return false;
        }
     }

   else
     {
      if(Allow_Multiple_Trades_On_Same_Candle == false)
        {
         for(int i=OrdersTotal()-1;i>=0;i--)
           {
            if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
              {
               if((OrderOpenTime()>=iTime(_Symbol,_Period,0)) && OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
                 {
                  if(OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP)
                    {
                     return false;
                    }
                 }
              }
           }
         for(int i=OrdersHistoryTotal()-1;i>=0;i--)
           {
            if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)==true)
              {
               if((OrderOpenTime()>=iTime(_Symbol,_Period,0)) && OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
                 {
                  if(OrderType() == OP_BUY || OrderType() == OP_SELL)
                    {
                     return false;
                    }
                 }
              }
           }
        }

      if(Allow_Only_On_Different_SuperTrend == true)
        {
         if(check_same_last_trd_st(magic_no))
           {
            return false;
           }
        }

      if(Allow_Entry_on_Other_Candle_While_This_Trade_is_Open == false)
        {
         if(Tot_TradesSpecific(magic_no) > 0)
           {
            return false;
           }
        }
     }

   return true;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Tot_TradesAll()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT)
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Tot_TradesSpecific(int magic)
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== magic))
           {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT)
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_same_last_trd_st(int no)
  {
   int last_no = last_trd_super_trend_no();
   if(last_no != 0 && last_no == no)
     {
      return true;
     }
   return false;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Modify_Stop()
  {
   int digits = SymbolInfoInteger(Symbol(),SYMBOL_DIGITS);
   double point =  SymbolInfoDouble(Symbol(),SYMBOL_POINT);
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if(OrderType() == OP_BUYSTOP)
              {

               double min_trailing_buffer_perc = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK) + (TrailingStopOrderBufferPercentage/100)*SymbolInfoDouble(_Symbol,SYMBOL_ASK),digits);
               double min_atr = atrpct[1]*Trailing_ATR_Multiplier;
               double entry_price = NormalizeDouble(MathMax(min_trailing_buffer_perc,min_atr),digits);

               if(entry_price<NormalizeDouble(OrderOpenPrice(),digits))
                 {
                  double new_sl = 0;
                  double new_tp = 0;
                  int sl_points = MathAbs(NormalizeDouble(OrderOpenPrice()-OrderStopLoss(),digits)/point);
                  int tp_points = MathAbs(NormalizeDouble(OrderOpenPrice()-OrderTakeProfit(),digits)/point);
                  if(OrderStopLoss()>0)
                    {
                     new_sl = NormalizeDouble(entry_price - sl_points*point,digits);
                    }
                  if(OrderTakeProfit()>0)
                    {
                     new_tp = NormalizeDouble(entry_price + tp_points*point,digits);
                    }
                  Print("<<<<<<<<<<------------------ Moduify Buy Stop ------------------>>>>>>>>>>>>>>");
                  OrderModify(OrderTicket(),entry_price,new_sl,new_tp,0,clrNONE);
                 }
              }
            if(OrderType() == OP_SELLSTOP)
              {
               double min_trailing_buffer_perc = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - (TrailingStopOrderBufferPercentage/100)*SymbolInfoDouble(_Symbol,SYMBOL_BID),digits);
               double min_atr = atrpct[1]*Trailing_ATR_Multiplier;
               double entry_price = NormalizeDouble(MathMin(min_trailing_buffer_perc,min_atr),digits);

               if(entry_price>NormalizeDouble(OrderOpenPrice(),digits))
                 {
                  double new_sl = 0;
                  double new_tp = 0;
                  int sl_points = MathAbs(NormalizeDouble(OrderOpenPrice()-OrderStopLoss(),digits)/point);
                  int tp_points = MathAbs(NormalizeDouble(OrderOpenPrice()-OrderTakeProfit(),digits)/point);
                  if(OrderStopLoss()>0)
                    {
                     new_sl = NormalizeDouble(entry_price + sl_points*point,digits);
                    }
                  if(OrderTakeProfit()>0)
                    {
                     new_tp = NormalizeDouble(entry_price - tp_points*point,digits);
                    }
                  Print("<<<<<<<<<<------------------ Moduify Buy Stop ------------------>>>>>>>>>>>>>>");
                  OrderModify(OrderTicket(),entry_price,new_sl,new_tp,0,clrNONE);
                 }
              }
           }
        }
     }
  }







//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int last_trd_super_trend_no()
  {
   datetime opn_tm_actv = -1;
   int actv_magic = 0;
   datetime opn_tm_closed = -1;
   int closed_magic = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP)
              {
               opn_tm_actv = OrderOpenTime();
               actv_magic = OrderMagicNumber();
              }
           }
        }
     }
   for(int i=OrdersHistoryTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP)
              {
               opn_tm_closed = OrderOpenTime();
               closed_magic = OrderMagicNumber();
              }
           }
        }
     }
   if(actv_magic == 0 && closed_magic == 0)
     {
      return 0;
     }
   if(opn_tm_actv>opn_tm_closed)
     {
      return actv_magic;
     }
   return closed_magic;

  }





//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Check_Simultenous_Trade()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP|| OrderType() == OP_BUYLIMIT|| OrderType() == OP_SELLLIMIT))
              {
               cnt++;
              }
           }
        }
     }
   return(cnt<Maximum_No_Of_Trades_Simultenously);
  }




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int History_Trades_On_Candle()
  {
   int cnt = 0;
   for(int i=OrdersHistoryTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderOpenTime()>=iTime(_Symbol,_Period,0)) && (OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Active_Trades_On_Candle()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderOpenTime()>=iTime(_Symbol,_Period,0)) && (OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Trades_Total()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Trades_Total_Actv()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderType() == OP_BUY || OrderType() == OP_SELL))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Trades_Total_Pend()
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Close_Opposite()
  {
   if(Trades_Total_Actv()>0)
     {
      Close_Pending_ALL();
     }
  }




//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Max_No_Of_Trades_On_Current_Candle(int Ord_Type)
  {
   int cnt = 0;
   if(HistorySelect(iTime(_Symbol,Default_Candle_TimeFrame,0), TimeCurrent()))
     {
      for(int i=HistoryDealsTotal()-1; i>=0; i--)
        {
         ulong ticket=HistoryDealGetTicket(i);
         string symbol = HistoryDealGetString(ticket,DEAL_SYMBOL);
         int magic = HistoryDealGetInteger(ticket,DEAL_MAGIC);
         if(HistoryDealGetInteger(ticket,DEAL_ENTRY) == DEAL_ENTRY_IN && symbol == _Symbol && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            cnt++;
           }
        }
     }
   return cnt;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Tot_Trades(int Ord_1, int Ord_2)
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderOpenTime()>=iTime(_Symbol,Default_Candle_TimeFrame,0)) && (OrderType() == Ord_1 || OrderType() == Ord_2))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int Tot_Trades(int Ord_Typ)
  {
   int cnt = 0;
   for(int i=OrdersTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_Addon || OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if((OrderType() == Ord_Typ))
              {
               cnt++;
              }
           }
        }
     }
   return cnt;
  }  


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool Last_Trade_Close_In_Loss(int Ord_Type)
  {
   for(int i=OrdersHistoryTotal()-1;i>=0;i--)
     {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)==true)
        {
         if(OrderSymbol() == Symbol() && (OrderMagicNumber()== Magic_1 || OrderMagicNumber()== Magic_2 || OrderMagicNumber()== Magic_3))
           {
            if(OrderCloseTime()<iTime(_Symbol,Default_Candle_TimeFrame,0))
              {
               return false;
              }
            //Print("   ---- >  ",i,"  ",OrdersHistoryTotal());
            if((OrderType() == Ord_Type)  && (OrderOpenTime()>=iTime(_Symbol,Default_Candle_TimeFrame,0)))
              {
               if((OrderProfit()+OrderCommission()+OrderSwap())<0)
                 {
                  return true;
                 }
               return false;
              }
            else
              {
               return false;
              }

           }
        }
     }
   return false;
  }

//ENUM_TIMEFRAMES GetTimeframeFromString(string tf)
//{
//
//   if(tf == "M1")    return PERIOD_M1;
//   if(tf == "M2")    return PERIOD_M2;
//   if(tf == "M3")    return PERIOD_M3;
//   if(tf == "M4")    return PERIOD_M4;
//   if(tf == "M5")    return PERIOD_M5;
//   if(tf == "M6")    return PERIOD_M6;
//   if(tf == "M10")   return PERIOD_M10;
//   if(tf == "M12")   return PERIOD_M12;
//   if(tf == "M15")   return PERIOD_M15;
//   if(tf == "M20")   return PERIOD_M20;
//   if(tf == "M30")   return PERIOD_M30;
//   if(tf == "H1")    return PERIOD_H1;
//   if(tf == "H2")    return PERIOD_H2;
//   if(tf == "H3")    return PERIOD_H3;
//   if(tf == "H4")    return PERIOD_H4;
//   if(tf == "H6")    return PERIOD_H6;
//   if(tf == "H8")    return PERIOD_H8;
//   if(tf == "H12")   return PERIOD_H12;
//   if(tf == "D1")    return PERIOD_D1;
//   if(tf == "W1")    return PERIOD_W1;
//   if(tf == "MN1")   return PERIOD_MN1;
//
//   return (ENUM_TIMEFRAMES)-1;
//}
bool Check_All_Magic(int magic_number)
{
 if(magic_number == Magic_1 || magic_number == Magic_2 || magic_number == Magic_3)
 {
  return true;
 }
 return false; 
}

void Candle_Based_BE()
{
  double point = SymbolInfoDouble(_Symbol,SYMBOL_POINT);
  int digits = SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
  
  if(!Enable_Candle_Structure_BE) return;
  double highest = iHigh(_Symbol,Candle_BE_Timeframe,1);
  double lowest = iLow(_Symbol,Candle_BE_Timeframe,1);
  for(int i = 1; i<=Candle_BE_Lookback_Count; i++)
  {
   if(iHigh(_Symbol,Candle_BE_Timeframe,i)>highest)
   {
    highest = iHigh(_Symbol,Candle_BE_Timeframe,i);
   }
   if(iLow(_Symbol,Candle_BE_Timeframe,i)<lowest)
   {
    lowest = iLow(_Symbol,Candle_BE_Timeframe,i);
   }   
  }  
   double highest1 = highest;
   double lowest1 = lowest;
   highest = NormalizeDouble(highest+(Candle_BE_Close_Above_Buffer_Percent/100)*highest,digits);    
   lowest = NormalizeDouble(lowest-(Candle_BE_Close_Above_Buffer_Percent/100)*lowest,digits);    
   bool high_break = iClose(_Symbol,_Period,1)>highest;
   bool low_break  = iClose(_Symbol,_Period,1)<lowest;
   if(high_break || low_break)
   {
     for(int i =OrdersTotal()-1 ; i>=0 ; i--)
        {
         if(
            (OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true) &&
            (OrderSymbol() == _Symbol) && 
            (OrderType() == OP_BUY || OrderType() == OP_SELL) &&
            Check_All_Magic(OrderMagicNumber())
           )
           {
               string comment = OrderComment();
               string outputArray[];
               int arraySize = StringSplit(comment, ',', outputArray);
               string target_SL_points = comment;
               if(arraySize > 0)
                 {
                  target_SL_points = outputArray[0];
                 }
               int sl_points = StringToInteger(target_SL_points);
               if(OrderType() == OP_BUY && high_break && OrderStopLoss()<OrderOpenPrice())
               {
                  double profit = NormalizeDouble(OrderClosePrice() - OrderOpenPrice(),digits)/point;
                  double expected_profit = sl_points*Min_BE_Distance_Multiplier;
                  if(!Use_Min_BE_Distance_Filter ||  profit >= expected_profit)
                    {
                     double new_sl = NormalizeDouble(iLow(_Symbol, _Period, 1)*(1-Candle_BE_SL_Buffer_Percent/100), digits);
                     if(new_sl <= NormalizeDouble(OrderClosePrice()-SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*point,digits) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           if(Journal_Candle_BE_Logic)
                             {
                               Print("================== [BE Triggerd] Long Trade ================== ");
                               Print(" BreakOut Confirmed On "+EnumToString(Candle_BE_Timeframe));
                               Print(" Structure: Highest High of the last "+IntegerToString(Candle_BE_Lookback_Count)+" candles = "+DoubleToString(highest1,digits));
                               Print(" Structure: Highest High After Adding "+DoubleToString(Candle_BE_Close_Above_Buffer_Percent)+" % = "+DoubleToString(highest,digits));
                               Print(" Last Candle Close Of Current Chart TimeFrame Candle = "+DoubleToString(iClose(_Symbol,_Period,1),digits));
                               if(Use_Min_BE_Distance_Filter)
                               {
                                Print("  Minimum SL Distance Passed ");
                                Print("Sl Points "+sl_points);
                                Print("Sl Points After Multiply With "+Min_BE_Distance_Multiplier+"  = "+expected_profit);
                                Print("Current Profit Point "+profit);
                               }
                               else 
                               {
                                Print("  Minimum SL Distance Check Not Used ");
                               }
                               Print(" Trigger Candle Low = "+DoubleToString(iLow(_Symbol, _Period, 1),digits));
                               Print(" New SL ==> Trigger Candle Low - "+Candle_BE_SL_Buffer_Percent+"%  = "+DoubleToString(new_sl,digits));
                               Print("=================================================== ");
                             }
                             //ExpertRemove();
                          }
                       }
                    }
               }
               if(OrderType() == OP_SELL && low_break && OrderStopLoss()>OrderOpenPrice())
               {
                  double profit = NormalizeDouble(OrderOpenPrice() - OrderClosePrice(),digits)/point;
                  double expected_profit = sl_points*Min_BE_Distance_Multiplier;
                  if(!Use_Min_BE_Distance_Filter ||  profit >= expected_profit)
                    {
                     double new_sl = NormalizeDouble(iHigh(_Symbol, _Period, 1)*(1+Candle_BE_SL_Buffer_Percent/100), digits);
                     if(new_sl >= NormalizeDouble(OrderClosePrice()+SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL)*point,digits) && (new_sl <OrderStopLoss() || OrderStopLoss() == 0))
                       {
                        if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                          {
                           if(Journal_Candle_BE_Logic)
                             {
                                Print("================== [BE Triggerd] Short Trade ================== ");
                               Print(" BreakOut Confirmed On "+EnumToString(Candle_BE_Timeframe));
                               Print(" Structure: Lowest Low of the last "+IntegerToString(Candle_BE_Lookback_Count)+" candles = "+DoubleToString(lowest1,digits));
                               Print(" Structure: Lowest Low After Subtracting "+DoubleToString(Candle_BE_Close_Above_Buffer_Percent)+" % = "+DoubleToString(lowest,digits));
                               Print(" Last Candle Close Of Current Chart TimeFrame Candle = "+DoubleToString(iClose(_Symbol,_Period,1),digits));
                               if(Use_Min_BE_Distance_Filter)
                               {
                                Print("  Minimum SL Distance Passed ");
                                Print("Sl Points "+sl_points);
                                Print("Sl Points After Multiply With "+Min_BE_Distance_Multiplier+"  = "+expected_profit);
                                Print("Current Profit Point "+profit);
                               }
                               else 
                               {
                                Print("  Minimum SL Distance Check Not Used ");
                               }
                               Print(" Trigger Candle High = "+DoubleToString(iHigh(_Symbol, _Period, 1),digits));
                               Print(" New SL ==> Trigger Candle High + "+Candle_BE_SL_Buffer_Percent+"%  = "+DoubleToString(new_sl,digits));
                               Print("=================================================== ");
                             }
                             //ExpertRemove();
                          }
                       }
                    }
               }               
                 
           }
        }    
   }
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void AdOn_Trade()
{
  double point = SymbolInfoDouble(_Symbol,SYMBOL_POINT);
  int digits = SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
 for(int i = OrdersTotal()-1; i>=0; i--)
 {
  if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES))
  {
   if(OrderSymbol() == _Symbol && Check_All_Magic(OrderMagicNumber()) && (OrderType() == OP_BUY || OrderType() == OP_SELL))
   {
    if(Check_Opened_AddOn(OrderTicket(),OrderOpenTime()))
    {
      OrderSelect(i,SELECT_BY_POS,MODE_TRADES);
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
      string comment = OrderComment();
      string outputArray[];
      int arraySize = StringSplit(comment, ',', outputArray);
      string target_SL_points = comment;
      if(arraySize > 0)
        {
         target_SL_points = outputArray[0];
        }
      int sl_points = StringToInteger(target_SL_points);   
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+      
      if(OrderType() == OP_BUY && OrderStopLoss()>OrderOpenPrice())
       {
        int parent_trade_sl_points = sl_points;
        int parent_trade_sl_locked_points = NormalizeDouble(OrderStopLoss()-OrderOpenPrice(),digits)/point; 
        if(parent_trade_sl_locked_points >= (sl_points*SL_Profit_Trigger_Multiplier))
        {
         double open_price = NormalizeDouble(OrderOpenPrice()+(sl_points*AddOn_Trigger_At_RR_Multiple)*point,digits);
         double open_price_with_buffer = open_price*(1+AddOn_Entry_Buffer_Percent/100);
         int slpoints_pend = NormalizeDouble(open_price_with_buffer - OrderStopLoss(),digits)/point;
         double take_profit = 0;
         if(AddOn_Use_Own_TP)
         {
          take_profit = NormalizeDouble(open_price_with_buffer + AddOn_TP_Multiplier*slpoints_pend*point,digits);
         }
         double pend_lots = AlignLots(NormalizeDouble(AddOn_Risk_Multiplier*OrderLots(),2));
         if(OrderSend(OrderSymbol(),OP_BUYSTOP,pend_lots,open_price_with_buffer,50,OrderStopLoss(),take_profit,slpoints_pend+"_"+OrderTicket(),Magic_Addon,0,clrNONE)>0)
         {
          //ExpertRemove();
            string log_msg =  "Buy Stop Placed - Symbol: "+_Symbol+", Time: "+TimeCurrent()+", Parent Trade SL locked Points: "+parent_trade_sl_locked_points+" Parent Trade Initial SL Points :"+sl_points+"\n"
            +"  After Multiply With "+SL_Profit_Trigger_Multiplier+" =  "+(sl_points*SL_Profit_Trigger_Multiplier)+"\n"
            +AddOn_Trigger_At_RR_Multiple+"x SL level = "+open_price+" | Buffer = "+AddOn_Entry_Buffer_Percent+"% -> Buy Stop placed @ "+open_price_with_buffer+" when price reached "+SymbolInfoDouble(_Symbol,SYMBOL_ASK)+""+"\n"
            +"Position Size: "+pend_lots+" lot | SL: Same as Parent | TP: "+AddOn_TP_Multiplier+"x SL | Trailing: ON "+EnumToString(AddOn_Trailing_Mode)+""+"\n";
            if(AddOn_Journal_Enabled)
            {
             Print(log_msg);
            }
         }
         
        }
       }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+       
      if(OrderType() == OP_SELL && OrderStopLoss()<OrderOpenPrice())
       {
        int parent_trade_sl_points = sl_points;
        int parent_trade_sl_locked_points = NormalizeDouble(OrderOpenPrice()-OrderStopLoss(),digits)/point; 
        if(parent_trade_sl_locked_points >= (sl_points*SL_Profit_Trigger_Multiplier))
        {
         double open_price = NormalizeDouble(OrderOpenPrice()+(sl_points*AddOn_Trigger_At_RR_Multiple)*point,digits);
         double open_price_with_buffer = open_price*(1-AddOn_Entry_Buffer_Percent/100);
         int slpoints_pend = NormalizeDouble(OrderStopLoss()-open_price_with_buffer,digits)/point;
         double take_profit = 0;
         if(AddOn_Use_Own_TP)
         {
          take_profit = NormalizeDouble(open_price_with_buffer - AddOn_TP_Multiplier*slpoints_pend*point,digits);
         }
         double pend_lots = AlignLots(NormalizeDouble(AddOn_Risk_Multiplier*OrderLots(),2));
         if(OrderSend(OrderSymbol(),OP_SELLSTOP,pend_lots,open_price_with_buffer,50,OrderStopLoss(),take_profit,slpoints_pend+"_"+OrderTicket(),Magic_Addon,0,clrNONE)>0)
         {
            string log_msg =  "Sell Stop Placed - Symbol: "+_Symbol+", Time: "+TimeCurrent()+", Parent Trade SL locked Points: "+parent_trade_sl_locked_points+" Parent Trade Initial SL Points :"+sl_points+"\n"
            +"  After Multiply With "+SL_Profit_Trigger_Multiplier+" =  "+(sl_points*SL_Profit_Trigger_Multiplier)+"\n"
            +AddOn_Trigger_At_RR_Multiple+"x SL level = "+open_price+" | Buffer = "+AddOn_Entry_Buffer_Percent+"% -> Sell Stop placed @ "+open_price_with_buffer+" when price reached "+SymbolInfoDouble(_Symbol,SYMBOL_BID)+""+"\n"
            +"Position Size: "+pend_lots+" lot | SL: Same as Parent | TP: "+AddOn_TP_Multiplier+"x SL | Trailing: ON "+EnumToString(AddOn_Trailing_Mode)+""+"\n";
            if(AddOn_Journal_Enabled)
            {
             Print(log_msg);
            }
         }
        }
       }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
     }       
   }
  }
 }
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Expire_AddOn_Pend()
{
 for(int i = OrdersTotal()-1; i>=0; i--)
 {
  if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES))
  {
   if(OrderSymbol() == _Symbol && OrderMagicNumber()==Magic_Addon && (OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP) && TimeCurrent()>=(OrderOpenTime()+AddOn_Cancel_Hours*60*60))
   {
     OrderDelete(OrderTicket());
   }
  }
 }  
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool  Check_Opened_AddOn(string main_ticket,datetime opentime)
{
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
 int active = 0;
 int pending = 0;
 int close_active = 0;
 int close_pending = 0;
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+ 
 for(int i = PositionsTotal()-1;i>=0;i--)
 {
  ulong ticket = PositionGetTicket(i);
  if(ticket>0)
  {
   if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == Magic_Addon && StringFind(PositionGetString(POSITION_COMMENT),main_ticket)>=0)
   {
    active++;
    return false;
   }
  }
 }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+ 
 for(int i = OrdersTotal()-1;i>=0;i--)
 {
  ulong ticket = OrderGetTicket(i);
  if(ticket>0)
  {
   if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == Magic_Addon && StringFind(OrderGetString(ORDER_COMMENT),main_ticket)>=0)
   {
    pending++;
    return false;
   }
  }
 }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
 if(HistorySelect(opentime,TimeCurrent()))
 {
   for(int i = HistoryDealsTotal()-1; i>=0 ; i--)
   {
     ulong ticket = HistoryDealGetTicket(i);
    // Print(ticket,"   ",HistoryDealGetString(ticket,DEAL_COMMENT));
     if(ticket>0)
     {
      if(HistoryDealGetString(ticket,DEAL_SYMBOL) == _Symbol && HistoryDealGetInteger(ticket,DEAL_MAGIC) == Magic_Addon && StringFind(HistoryDealGetString(ticket,DEAL_COMMENT),main_ticket)>=0 && HistoryDealGetInteger(ticket,DEAL_ENTRY) == DEAL_ENTRY_IN)
      {
       return false;
      }
     }
   }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   for(int i = HistoryOrdersTotal()-1; i>=0 ; i--)
   {
     ulong ticket = HistoryOrderGetTicket(i);
     if(ticket>0)
     {
      //Print(ticket,"   ",HistoryOrderGetInteger(ticket,ORDER_STATE));
      if(HistoryOrderGetString(ticket,ORDER_SYMBOL) == _Symbol && HistoryOrderGetInteger(ticket,ORDER_MAGIC) == Magic_Addon && StringFind(HistoryOrderGetString(ticket,ORDER_COMMENT),main_ticket)>=0 && (HistoryOrderGetInteger(ticket,ORDER_STATE) == ORDER_STATE_CANCELED || HistoryOrderGetInteger(ticket,ORDER_STATE) == ORDER_STATE_EXPIRED))
      {
       close_pending++;
       if(close_pending>=AddOn_Max_Attempts)
       {
        return false;
       }
      }
     }
   }   
 }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+ 
  return true;
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void AddOn_Trailing()
  { 
   ENUM_TIMEFRAMES Trail_TF = AddOn_Trailing_TF;
   double Buffer_Perc = AddOn_Trailing_Buffer;
   if(AddOn_Use_Own_Trailing)
     {
      bool Cnd_Conf = false;
      if(AddOn_Trailing_Candle_Color == Cand_Any)
        {
         Cnd_Conf = true;
        }
      if(AddOn_Trailing_Candle_Color == Cand_Green)
        {
         Cnd_Conf = (iClose(_Symbol,Trail_TF,1)>iOpen(_Symbol,Trail_TF,1)); 
        }
      if(AddOn_Trailing_Candle_Color == Cand_Red)
        {
         Cnd_Conf = (iClose(_Symbol,Trail_TF,1)<iOpen(_Symbol,Trail_TF,1));          
        }
        
      if(Cnd_Conf)
        {
         for(int i = OrdersTotal()-1 ; i>=0 ; i--)
           {
            if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
              {
               if((OrderMagicNumber() == Magic_Addon) && OrderSymbol() == _Symbol)
                 {
                  string comment = OrderComment();
                  string outputArray[];
                  int arraySize = StringSplit(comment, ',', outputArray);
                  string target_SL_points = comment;
                  if(arraySize > 0)
                    {
                     target_SL_points = outputArray[0];
                    }

                  int sl_points = StringToInteger(target_SL_points);


                  if(OrderType() == OP_BUY)
                    {
                     double profit = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID) - OrderOpenPrice(),_Digits)/_Point;
                     double expected_profit = sl_points*tp_mult_1;
                     if(profit >= expected_profit)
                       {
                        double new_sl = 0;
                        
                        if(AddOn_Trailing_Mode == Trail_By_Candle)
                        {
                         new_sl = NormalizeDouble(iLow(NULL, Trail_TF, 1)*(1-Buffer_Perc/100), _Digits);
                        }
                        if(AddOn_Trailing_Mode == Trail_By_Percent)
                        {
                         new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_BID)*(1-Buffer_Perc/100), _Digits);
                        }
                       
                        if(new_sl < SymbolInfoDouble(_Symbol,SYMBOL_BID) && (new_sl >OrderStopLoss() || OrderStopLoss() == 0))
                          {
                           if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                             {
                              if(AddOn_Journal_Enabled)
                                {
                                 Print(" AdOn Trailing ");
                                }
                             }
                          }
                       }
                    }
                  else
                     if(OrderType()==OP_SELL)
                       {
                        double profit = NormalizeDouble(OrderOpenPrice() - SymbolInfoDouble(_Symbol,SYMBOL_ASK),_Digits)/_Point;
                        double expected_profit = sl_points*tp_mult_1;
                        if(profit >= expected_profit)
                          {
                           double new_sl = 0;
                           
                           if(AddOn_Trailing_Mode == Trail_By_Candle)
                           {
                            new_sl = NormalizeDouble(iHigh(NULL, Trail_TF, 1)*(1+Buffer_Perc/100), _Digits);
                           }
                           if(AddOn_Trailing_Mode == Trail_By_Percent)
                           {
                            new_sl = NormalizeDouble(SymbolInfoDouble(_Symbol,SYMBOL_ASK)*(1+Buffer_Perc/100), _Digits);
                           }
                           
                           
                           if(new_sl > SymbolInfoDouble(_Symbol,SYMBOL_ASK) && (new_sl < OrderStopLoss() || OrderStopLoss() == 0))
                             {
                    
                              if(OrderModify(OrderTicket(),OrderOpenPrice(), new_sl, OrderTakeProfit(),0,clrNONE))
                                {
                                 if(AddOn_Journal_Enabled)
                                   {
                                    Print(" AdOn Trailing ");
                                   }
                                }
                             }
                          }
                       }
                 }

              }
           }
        }
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool RectLabelCreate()
  {
   const long             chart_ID=0;          
   const string           name=dashboard_prefix+"RectLabel";    
   const int              sub_window=0;        
   const int              x=0;                 
   const int              y=0;                 
   const int              width=500;            
   const int              height=500;           
   const color            back_clr=C'70,130,180';
   const ENUM_BORDER_TYPE border=BORDER_SUNKEN;    
   const ENUM_BASE_CORNER corner=CORNER_LEFT_UPPER;
   const color            clr=C'70,130,180';              
   const ENUM_LINE_STYLE  style=STYLE_SOLID;       
   const int              line_width=1;            
   const bool             back=false;              
   const bool             selection=false;         
   const bool             hidden=true;
   const long             z_order=0;
   ObjectCreate(chart_ID,name,OBJ_RECTANGLE_LABEL,sub_window,0,0);
   ObjectSetInteger(chart_ID,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(chart_ID,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(chart_ID,name,OBJPROP_XSIZE,width);
   ObjectSetInteger(chart_ID,name,OBJPROP_YSIZE,height);
   ObjectSetInteger(chart_ID,name,OBJPROP_BGCOLOR,back_clr);
   ObjectSetInteger(chart_ID,name,OBJPROP_BORDER_TYPE,border);
   ObjectSetInteger(chart_ID,name,OBJPROP_CORNER,corner);
   ObjectSetInteger(chart_ID,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(chart_ID,name,OBJPROP_STYLE,style);
   ObjectSetInteger(chart_ID,name,OBJPROP_WIDTH,line_width);
   ObjectSetInteger(chart_ID,name,OBJPROP_BACK,back);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTABLE,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTED,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_HIDDEN,hidden);
   ObjectSetInteger(chart_ID,name,OBJPROP_ZORDER,z_order);
   return(true);
  }  
  
bool LabelCreate(const string name,const int x,const int y,const string text,const int font_size,const color clr,const string font)
  {
  const long              chart_ID=0; 
  const int               sub_window=0;        
  const ENUM_BASE_CORNER  corner=CORNER_LEFT_UPPER;                                                   
  const double            angle=0.0;                
  const ENUM_ANCHOR_POINT anchor=ANCHOR_LEFT_UPPER; 
  const bool              back=false;               
  const bool              selection=false;          
  const bool              hidden=true;              
  const long              z_order=0;
   ObjectDelete(chart_ID,name);
   ObjectCreate(chart_ID,name,OBJ_LABEL,sub_window,0,0);
   ObjectSetInteger(chart_ID,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(chart_ID,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(chart_ID,name,OBJPROP_CORNER,corner);
   ObjectSetString(chart_ID,name,OBJPROP_TEXT,text);
   ObjectSetString(chart_ID,name,OBJPROP_FONT,font);
   ObjectSetInteger(chart_ID,name,OBJPROP_FONTSIZE,font_size);
   ObjectSetDouble(chart_ID,name,OBJPROP_ANGLE,angle);
   ObjectSetInteger(chart_ID,name,OBJPROP_ANCHOR,anchor);
   ObjectSetInteger(chart_ID,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(chart_ID,name,OBJPROP_BACK,back);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTABLE,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTED,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_HIDDEN,hidden);
   ObjectSetInteger(chart_ID,name,OBJPROP_ZORDER,z_order);
   return(true);
  }   
  
  
bool Check_Commander(string symb)
{
 if(!CommanderCheck || MQLInfoInteger(MQL_TESTER)) return true;
 string cicsymb[];
 string cicstatus[];
 string cicreason[];
 string filename = "CIC.csv";
 int filehandle=FileOpen(filename,FILE_READ|FILE_CSV|FILE_COMMON|FILE_ANSI,",");
 if(filehandle>=0)
 {         
   while(!FileIsEnding(filehandle))
   {
     Array_Fill(cicsymb,FileReadString(filehandle));
     Array_Fill(cicstatus,FileReadString(filehandle));
     Array_Fill(cicreason,FileReadString(filehandle));
   }
   FileClose(filehandle);
   for(int i = 0; i<ArraySize(cicsymb);i++)
   {
      if(symb == cicsymb[i])
      {
       if(cicstatus[i] == "No")
       {
         Print("Commander Blocked Reason : "+cicreason[i]);
         return false;
       }
       else
       {
         return true;
       }
      }  
   }
 }
else
  {
   Print(" =========  File Open Error   =========");
  }
  return true;        
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  
void Array_Fill(string &arr[], string val)
{
 ArrayResize(arr,ArraySize(arr)+1);
 arr[ArraySize(arr)-1] = val;
}
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
//======================================================================================================================//
//""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""//
//------------------------------------------------- News Filter -------------------------------------------------------//
//+------------------------------------------------------------------+
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//---------------------------       JSON   -------------------------------------------------------------------//
#define DEBUG_PRINT false
//------------------------------------------------------------------ enum enJAType
enum enJAType { jtUNDEF,jtNULL,jtBOOL,jtINT,jtDBL,jtSTR,jtARRAY,jtOBJ };
//------------------------------------------------------------------ class CJAVal
class CJAVal
  {
public:
   virtual void      Clear() { m_parent=NULL; m_key=""; m_type=jtUNDEF; m_bv=false; m_iv=0; m_dv=0; m_sv=""; ArrayResize(m_e,0); }
   virtual bool      Copy(const CJAVal &a) { m_key=a.m_key; CopyData(a); return true; }
   virtual void      CopyData(const CJAVal &a) { m_type=a.m_type; m_bv=a.m_bv; m_iv=a.m_iv; m_dv=a.m_dv; m_sv=a.m_sv; CopyArr(a); }
   virtual void      CopyArr(const CJAVal &a) { int n=ArrayResize(m_e,ArraySize(a.m_e)); for(int i=0; i<n; i++) { m_e[i]=a.m_e[i]; m_e[i].m_parent=GetPointer(this); } }

public:
   CJAVal            m_e[];
   string            m_key;
   string            m_lkey;
   CJAVal            *m_parent;
   enJAType          m_type;
   bool              m_bv;
   long              m_iv;
   double            m_dv;
   string            m_sv;
   static int        code_page;

public:
                     CJAVal() { Clear(); }
                     CJAVal(CJAVal *aparent,enJAType atype) { Clear(); m_type=atype; m_parent=aparent; }
                     CJAVal(enJAType t,string a) { Clear(); FromStr(t,a); }
                     CJAVal(const int a) { Clear(); m_type=jtINT; m_iv=a; m_dv=(double)m_iv; m_sv=IntegerToString(m_iv); m_bv=m_iv!=0; }
                     CJAVal(const long a) { Clear(); m_type=jtINT; m_iv=a; m_dv=(double)m_iv; m_sv=IntegerToString(m_iv); m_bv=m_iv!=0; }
                     CJAVal(const double a) { Clear(); m_type=jtDBL; m_dv=a; m_iv=(long)m_dv; m_sv=DoubleToString(m_dv); m_bv=m_iv!=0; }
                     CJAVal(const bool a) { Clear(); m_type=jtBOOL; m_bv=a; m_iv=m_bv; m_dv=m_bv; m_sv=IntegerToString(m_iv); }
                     CJAVal(const CJAVal &a) { Clear(); Copy(a); }
                    ~CJAVal() { Clear(); }

public:
   virtual bool      IsNumeric() { return m_type==jtDBL || m_type==jtINT; }
   virtual CJAVal    *FindKey(string akey) { for(int i=ArraySize(m_e)-1; i>=0; --i) if(m_e[i].m_key==akey) return GetPointer(m_e[i]); return NULL; }
   virtual CJAVal    *HasKey(string akey,enJAType atype=jtUNDEF);
   virtual CJAVal   *operator[](string akey);
   virtual CJAVal   *operator[](int i);
   void              operator=(const CJAVal &a) { Copy(a); }
   void              operator=(const int a) { m_type=jtINT; m_iv=a; m_dv=(double)m_iv; m_bv=m_iv!=0; }
   void              operator=(const long a) { m_type=jtINT; m_iv=a; m_dv=(double)m_iv; m_bv=m_iv!=0; }
   void              operator=(const double a) { m_type=jtDBL; m_dv=a; m_iv=(long)m_dv; m_bv=m_iv!=0; }
   void              operator=(const bool a) { m_type=jtBOOL; m_bv=a; m_iv=(long)m_bv; m_dv=(double)m_bv; }
   void              operator=(string a) { m_type=(a!=NULL)?jtSTR:jtNULL; m_sv=a; m_iv=StringToInteger(m_sv); m_dv=StringToDouble(m_sv); m_bv=a!=NULL; }

   bool              operator==(const int a) { return m_iv==a; }
   bool              operator==(const long a) { return m_iv==a; }
   bool              operator==(const double a) { return m_dv==a; }
   bool              operator==(const bool a) { return m_bv==a; }
   bool              operator==(string a) { return m_sv==a; }

   bool              operator!=(const int a) { return m_iv!=a; }
   bool              operator!=(const long a) { return m_iv!=a; }
   bool              operator!=(const double a) { return m_dv!=a; }
   bool              operator!=(const bool a) { return m_bv!=a; }
   bool              operator!=(string a) { return m_sv!=a; }

   long              ToInt() const { return m_iv; }
   double            ToDbl() const { return m_dv; }
   bool              ToBool() const { return m_bv; }
   string            ToStr() { return m_sv; }

   virtual void      FromStr(enJAType t,string a)
     {
      m_type=t;
      switch(m_type)
        {
         case jtBOOL:
            m_bv=(StringToInteger(a)!=0);
            m_iv=(long)m_bv;
            m_dv=(double)m_bv;
            m_sv=a;
            break;
         case jtINT:
            m_iv=StringToInteger(a);
            m_dv=(double)m_iv;
            m_sv=a;
            m_bv=m_iv!=0;
            break;
         case jtDBL:
            m_dv=StringToDouble(a);
            m_iv=(long)m_dv;
            m_sv=a;
            m_bv=m_iv!=0;
            break;
         case jtSTR:
            m_sv=Unescape(a);
            m_type=(m_sv!=NULL)?jtSTR:jtNULL;
            m_iv=StringToInteger(m_sv);
            m_dv=StringToDouble(m_sv);
            m_bv=m_sv!=NULL;
            break;
        }
     }
   virtual string    GetStr(char &js[],int i,int slen)
     {
#ifdef __MQL4__
      if(slen<=0)
         return "";
#endif
      char cc[];
      ArrayCopy(cc,js,0,i,slen);
      return CharArrayToString(cc, 0, WHOLE_ARRAY, CJAVal::code_page);
     }

   virtual void      Set(const CJAVal &a) { if(m_type==jtUNDEF) m_type=jtOBJ; CopyData(a); }
   virtual void      Set(const CJAVal &list[]);
   virtual CJAVal    *Add(const CJAVal &item) { if(m_type==jtUNDEF) m_type=jtARRAY; /*ASSERT(m_type==jtOBJ || m_type==jtARRAY);*/ return AddBase(item); } // ??????????
   virtual CJAVal    *Add(const int a) { CJAVal item(a); return Add(item); }
   virtual CJAVal    *Add(const long a) { CJAVal item(a); return Add(item); }
   virtual CJAVal    *Add(const double a) { CJAVal item(a); return Add(item); }
   virtual CJAVal    *Add(const bool a) { CJAVal item(a); return Add(item); }
   virtual CJAVal    *Add(string a) { CJAVal item(jtSTR,a); return Add(item); }
   virtual CJAVal    *AddBase(const CJAVal &item) { int c=ArraySize(m_e); ArrayResize(m_e,c+1); m_e[c]=item; m_e[c].m_parent=GetPointer(this); return GetPointer(m_e[c]); } // ??????????
   virtual CJAVal    *New() { if(m_type==jtUNDEF) m_type=jtARRAY; /*ASSERT(m_type==jtOBJ || m_type==jtARRAY);*/ return NewBase(); } // ??????????
   virtual CJAVal    *NewBase() { int c=ArraySize(m_e); ArrayResize(m_e,c+1); return GetPointer(m_e[c]); } // ??????????

   virtual string    Escape(string a);
   virtual string    Unescape(string a);
public:
   virtual void      Serialize(string &js,bool bf=false,bool bcoma=false);
   virtual string    Serialize() { string js; Serialize(js); return js; }
   virtual bool      Deserialize(char &js[],int slen,int &i);
   virtual bool      ExtrStr(char &js[],int slen,int &i);
   virtual bool      Deserialize(string js,int acp=CP_ACP) { int i=0; Clear(); CJAVal::code_page=acp; char arr[]; int slen=StringToCharArray(js,arr,0,WHOLE_ARRAY,CJAVal::code_page); return Deserialize(arr,slen,i); }
   virtual bool      Deserialize(char &js[],int acp=CP_ACP) { int i=0; Clear(); CJAVal::code_page=acp; return Deserialize(js,ArraySize(js),i); }
  };

int CJAVal::code_page=CP_ACP;

//------------------------------------------------------------------ HasKey
CJAVal *CJAVal::HasKey(string akey,enJAType atype/*=jtUNDEF*/) { for(int i=0; i<ArraySize(m_e); i++) if(m_e[i].m_key==akey) { if(atype==jtUNDEF || atype==m_e[i].m_type) return GetPointer(m_e[i]); break; } return NULL; }
//------------------------------------------------------------------ operator[]
CJAVal *CJAVal::operator[](string akey) { if(m_type==jtUNDEF) m_type=jtOBJ; CJAVal *v=FindKey(akey); if(v) return v; CJAVal b(GetPointer(this),jtUNDEF); b.m_key=akey; v=Add(b); return v; }
//------------------------------------------------------------------ operator[]
CJAVal *CJAVal::operator[](int i)
  {
   if(m_type==jtUNDEF)
      m_type=jtARRAY;
   while(i>=ArraySize(m_e))
     {
      CJAVal b(GetPointer(this),jtUNDEF);
      if(CheckPointer(Add(b))==POINTER_INVALID)
         return NULL;
     }
   return GetPointer(m_e[i]);
  }
//------------------------------------------------------------------ Set
void CJAVal::Set(const CJAVal &list[])
  {
   if(m_type==jtUNDEF)
      m_type=jtARRAY;
   int n=ArrayResize(m_e,ArraySize(list));
   for(int i=0; i<n; ++i)
     {
      m_e[i]=list[i];
      m_e[i].m_parent=GetPointer(this);
     }
  }
//------------------------------------------------------------------ Serialize
void CJAVal::Serialize(string &js,bool bkey/*=false*/,bool coma/*=false*/)
  {
   if(m_type==jtUNDEF)
      return;
   if(coma)
      js+=",";
   if(bkey)
      js+=StringFormat("\"%s\":", m_key);
   int _n=ArraySize(m_e);
   switch(m_type)
     {
      case jtNULL:
         js+="null";
         break;
      case jtBOOL:
         js+=(m_bv?"true":"false");
         break;
      case jtINT:
         js+=IntegerToString(m_iv);
         break;
      case jtDBL:
         js+=DoubleToString(m_dv);
         break;
      case jtSTR:
        { string ss=Escape(m_sv); if(StringLen(ss)>0) js+=StringFormat("\"%s\"",ss); else js+="null"; }
      break;
      case jtARRAY:
         js+="[";
         for(int i=0; i<_n; i++)
            m_e[i].Serialize(js,false,i>0);
         js+="]";
         break;
      case jtOBJ:
         js+="{";
         for(int i=0; i<_n; i++)
            m_e[i].Serialize(js,true,i>0);
         js+="}";
         break;
     }
  }
//------------------------------------------------------------------ Deserialize
bool CJAVal::Deserialize(char &js[],int slen,int &i)
  {
   string num="0123456789+-.eE";
   int i0=i;
   for(; i<slen; i++)
     {
      char c=js[i];
      if(c==0)
         break;
      switch(c)
        {
         case '\t':
         case '\r':
         case '\n':
         case ' ': // ?????????? ?? ????? ???????
            i0=i+1;
            break;

         case '[': // ?????? ???????. ??????? ??????? ? ???????? ?? js
           {
            i0=i+1;
            if(m_type!=jtUNDEF)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ???? ???????? ??? ????? ???, ?? ??? ??????
               return false;
              }
            m_type=jtARRAY; // ?????? ??? ????????
            i++;
            CJAVal val(GetPointer(this),jtUNDEF);
            while(val.Deserialize(js,slen,i))
              {
               if(val.m_type!=jtUNDEF)
                  Add(val);
               if(val.m_type==jtINT || val.m_type==jtDBL || val.m_type==jtARRAY)
                  i++;
               val.Clear();
               val.m_parent=GetPointer(this);
               if(js[i]==']')
                  break;
               i++;
               if(i>=slen)
                 {
                  if(DEBUG_PRINT)
                     Print(m_key+" "+string(__LINE__));
                  return false;
                 }
              }
            return js[i]==']' || js[i]==0;
           }
         break;
         case ']':
            if(!m_parent)
               return false;
            return m_parent.m_type==jtARRAY; // ????? ???????, ??????? ???????? ?????? ???? ????????

         case ':':
           {
            if(m_lkey=="")
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));
               return false;
              }
            CJAVal val(GetPointer(this),jtUNDEF);
            CJAVal *oc=Add(val); // ??? ??????? ???? ?? ?????????
            oc.m_key=m_lkey;
            m_lkey=""; // ?????? ??? ?????
            i++;
            if(!oc.Deserialize(js,slen,i))
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));
               return false;
              }
            break;
           }
         case ',': // ??????????? ???????? // ??? ???????? ??? ?????? ???? ?????????
            i0=i+1;
            if(!m_parent && m_type!=jtOBJ)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));
               return false;
              }
            else
               if(m_parent)
                 {
                  if(m_parent.m_type!=jtARRAY && m_parent.m_type!=jtOBJ)
                    {
                     if(DEBUG_PRINT)
                        Print(m_key+" "+string(__LINE__));
                     return false;
                    }
                  if(m_parent.m_type==jtARRAY && m_type==jtUNDEF)
                     return true;
                 }
            break;

         // ????????? ????? ???? ?????? ? ??????? / ???? ??????????????
         case '{': // ?????? ???????. ??????? ?????? ? ???????? ??? ?? js
            i0=i+1;
            if(m_type!=jtUNDEF)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ?????? ????
               return false;
              }
            m_type=jtOBJ; // ?????? ??? ????????
            i++;
            if(!Deserialize(js,slen,i))
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ?????????? ???
               return false;
              }
            return js[i]=='}' || js[i]==0;
            break;
         case '}':
            return m_type==jtOBJ; // ????? ???????, ??????? ???????? ?????? ???? ????????

         case 't':
         case 'T': // ?????? true
         case 'f':
         case 'F': // ?????? false
            if(m_type!=jtUNDEF)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ?????? ????
               return false;
              }
            m_type=jtBOOL; // ?????? ??? ????????
            if(i+3<slen)
              {
               if(StringCompare(GetStr(js, i, 4), "true", false)==0)
                 {
                  m_bv=true;
                  i+=3;
                  return true;
                 }
              }
            if(i+4<slen)
              {
               if(StringCompare(GetStr(js, i, 5), "false", false)==0)
                 {
                  m_bv=false;
                  i+=4;
                  return true;
                 }
              }
            if(DEBUG_PRINT)
               Print(m_key+" "+string(__LINE__));
            return false; // ?? ??? ??? ??? ????? ??????
            break;
         case 'n':
         case 'N': // ?????? null
            if(m_type!=jtUNDEF)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ?????? ????
               return false;
              }
            m_type=jtNULL; // ?????? ??? ????????
            if(i+3<slen)
               if(StringCompare(GetStr(js,i,4),"null",false)==0)
                 {
                  i+=3;
                  return true;
                 }
            if(DEBUG_PRINT)
               Print(m_key+" "+string(__LINE__));
            return false; // ?? NULL ??? ????? ??????
            break;

         case '0':
         case '1':
         case '2':
         case '3':
         case '4':
         case '5':
         case '6':
         case '7':
         case '8':
         case '9':
         case '-':
         case '+':
         case '.': // ?????? ?????
           {
            if(m_type!=jtUNDEF)
              {
               if(DEBUG_PRINT)
                  Print(m_key+" "+string(__LINE__));   // ?????? ????
               return false;
              }
            bool dbl=false;// ?????? ??? ????????
            int is=i;
            while(js[i]!=0 && i<slen)
              {
               i++;
               if(StringFind(num,GetStr(js,i,1))<0)
                  break;
               if(!dbl)
                  dbl=(js[i]=='.' || js[i]=='e' || js[i]=='E');
              }
            m_sv=GetStr(js,is,i-is);
            if(dbl)
              {
               m_type=jtDBL;
               m_dv=StringToDouble(m_sv);
               m_iv=(long)m_dv;
               m_bv=m_iv!=0;
              }
            else
              {
               m_type=jtINT;   // ??????? ??? ????????
               m_iv=StringToInteger(m_sv);
               m_dv=(double)m_iv;
               m_bv=m_iv!=0;
              }
            i--;
            return true; // ???????????? ?? 1 ?????? ????? ? ?????
            break;
           }
         case '\"': // ?????? ??? ????? ??????
            if(m_type==jtOBJ) // ???? ??? ??? ??????????? ? ???? ?? ?????
              {
               i++;
               int is=i;
               if(!ExtrStr(js,slen,i))
                 {
                  if(DEBUG_PRINT)
                     Print(m_key+" "+string(__LINE__));   // ??? ????, ???? ?? ????? ??????
                  return false;
                 }
               m_lkey=GetStr(js,is,i-is);
              }
            else
              {
               if(m_type!=jtUNDEF)
                 {
                  if(DEBUG_PRINT)
                     Print(m_key+" "+string(__LINE__));   // ?????? ????
                  return false;
                 }
               m_type=jtSTR; // ?????? ??? ????????
               i++;
               int is=i;
               if(!ExtrStr(js,slen,i))
                 {
                  if(DEBUG_PRINT)
                     Print(m_key+" "+string(__LINE__));
                  return false;
                 }
               FromStr(jtSTR,GetStr(js,is,i-is));
               return true;
              }
            break;
        }
     }
   return true;
  }
//------------------------------------------------------------------ ExtrStr
bool CJAVal::ExtrStr(char &js[],int slen,int &i)
  {
   for(; js[i]!=0 && i<slen; i++)
     {
      char c=js[i];
      if(c=='\"')
         break; // ????? ??????
      if(c=='\\' && i+1<slen)
        {
         i++;
         c=js[i];
         switch(c)
           {
            case '/':
            case '\\':
            case '\"':
            case 'b':
            case 'f':
            case 'r':
            case 'n':
            case 't':
               break; // ??? ???????????
            case 'u': // \uXXXX
              {
               i++;
               for(int j=0; j<4 && i<slen && js[i]!=0; j++,i++)
                 {
                  if(!((js[i]>='0' && js[i]<='9') || (js[i]>='A' && js[i]<='F') || (js[i]>='a' && js[i]<='f')))
                    {
                     if(DEBUG_PRINT)
                        Print(m_key+" "+CharToString(js[i])+" "+string(__LINE__));   // ?? hex
                     return false;
                    }
                 }
               i--;
               break;
              }
            default:
               break; /*{ return false; } // ????????????? ?????? ? ?????????????? */
           }
        }
     }
   return true;
  }
//------------------------------------------------------------------ Escape
string CJAVal::Escape(string a)
  {
   ushort as[], s[];
   int n=StringToShortArray(a, as);
   if(ArrayResize(s, 2*n)!=2*n)
      return NULL;
   int j=0;
   for(int i=0; i<n; i++)
     {
      switch(as[i])
        {
         case '\\':
            s[j]='\\';
            j++;
            s[j]='\\';
            j++;
            break;
         case '"':
            s[j]='\\';
            j++;
            s[j]='"';
            j++;
            break;
         case '/':
            s[j]='\\';
            j++;
            s[j]='/';
            j++;
            break;
         case 8:
            s[j]='\\';
            j++;
            s[j]='b';
            j++;
            break;
         case 12:
            s[j]='\\';
            j++;
            s[j]='f';
            j++;
            break;
         case '\n':
            s[j]='\\';
            j++;
            s[j]='n';
            j++;
            break;
         case '\r':
            s[j]='\\';
            j++;
            s[j]='r';
            j++;
            break;
         case '\t':
            s[j]='\\';
            j++;
            s[j]='t';
            j++;
            break;
         default:
            s[j]=as[i];
            j++;
            break;
        }
     }
   a=ShortArrayToString(s,0,j);
   return a;
  }
//------------------------------------------------------------------ Unescape
string CJAVal::Unescape(string a)
  {
   ushort as[], s[];
   int n=StringToShortArray(a, as);
   if(ArrayResize(s, n)!=n)
      return NULL;
   int j=0,i=0;
   while(i<n)
     {
      ushort c=as[i];
      if(c=='\\' && i<n-1)
        {
         switch(as[i+1])
           {
            case '\\':
               c='\\';
               i++;
               break;
            case '"':
               c='"';
               i++;
               break;
            case '/':
               c='/';
               i++;
               break;
            case 'b':
               c=8; /*08='\b'*/;
               i++;
               break;
            case 'f':
               c=12;/*0c=\f*/ i++;
               break;
            case 'n':
               c='\n';
               i++;
               break;
            case 'r':
               c='\r';
               i++;
               break;
            case 't':
               c='\t';
               i++;
               break;
               /*
               case 'u': // \uXXXX
                 {
                  i+=2; ushort k=0;
                  for(int jj=0; jj<4 && i<n; jj++,i++)
                    {
                     c=as[i]; ushort h=0;
                     if(c>='0' && c<='9') h=c-'0';
                     else if(c>='A' && c<='F') h=c-'A'+10;
                     else if(c>='a' && c<='f') h=c-'a'+10;
                     else break; // ?? hex
                     k+=h*(ushort)pow(16,(3-jj));
                    }
                  i--;
                  c=k;
                  break;
                 }
                 */
           }
        }
      s[j]=c;
      j++;
      i++;
     }
   a=ShortArrayToString(s,0,j);
   return a;
  }
//---------------------------       JSON   -------------------------------------------------------------------//
///////////////////////////////////////////////////////////////////////////////////////////////////////////////

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
datetime tm_h;

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void OnTimer()
  {
    
   if((Enable_Red_News_Filter || Enable_Special_Event_Close)  && !MQLInfoInteger(MQL_TESTER))
     {
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+     
      if(tm_h != iTime(Symbol(),PERIOD_H1,0))
        {
         Write_News_On_File();
         tm_h = iTime(Symbol(),PERIOD_H1,0);
        }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
      if(tmr != iTime(Symbol(),PERIOD_M1,0))
        {
         Read_From_File_Update_Var();
         tmr = iTime(Symbol(),PERIOD_M1,0);
        }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

      check_news();


      // ObjectSetString(0,"News_Count_Down_Re",OBJPROP_TEXT,"--");

      ObjectSetString(0,"News_Count_Down_Re",OBJPROP_TEXT,News_Title_Re!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Date_Re) - TimeGMT()))):"--");
      ObjectSetString(0,"News_Count_Down_Up",OBJPROP_TEXT,News_Title_Up!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Date_Up) - TimeGMT()))):"--");
      ObjectSetString(0,"News_Sp_Fomc_Count_Down_Re",OBJPROP_TEXT,News_Sp_Fomc_Title_Re!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Sp_Fomc_Date_Re) - TimeGMT()))):"--");
      ObjectSetString(0,"News_Sp_Fomc_Count_Down_Up",OBJPROP_TEXT,News_Sp_Fomc_Title_Up!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Sp_Fomc_Date_Up) - TimeGMT()))):"--");      
      ObjectSetString(0,"News_Sp_NFP_Count_Down_Re",OBJPROP_TEXT,News_Sp_NFP_Title_Re!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Sp_NFP_Date_Re) - TimeGMT()))):"--");
      ObjectSetString(0,"News_Sp_NFP_Count_Down_Up",OBJPROP_TEXT,News_Sp_NFP_Title_Up!=""?SecondsToTimeString(int(MathAbs(StringToTime(News_Sp_NFP_Date_Up) - TimeGMT()))):"--");       
      ObjectSetString(0,"News_Main",OBJPROP_TEXT,"Time GMT    "+TimeToString(TimeGMT(),TIME_DATE|TIME_MINUTES|TIME_SECONDS));

     }
  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Read_From_File_Update_Var()
  {
//+------------------------------------------------------------------+
//|          Initialize Standard News Variables                      |
//+------------------------------------------------------------------+  
   News_Title_Re = "";
   News_Date_Re = "";
   News_Currency_Re = "";
   News_Impact_Re = "";
   News_Previous_Re = "";
   News_Forecast_Re = "";
   News_Count_Down_Re = "";

   News_Title_Up = "";
   News_Date_Up = "";
   News_Currency_Up = "";
   News_Impact_Up = "";
   News_Previous_Up = "";
   News_Forecast_Up = "";
   News_Count_Down_Up = "";
   
   
//+------------------------------------------------------------------+
//|          Initialize Speacial FOMC News Variables                 |
//+------------------------------------------------------------------+  
   News_Sp_Fomc_Title_Re = "";
   News_Sp_Fomc_Date_Re = "";
   News_Sp_Fomc_Currency_Re = "";
   News_Sp_Fomc_Impact_Re = "";
   News_Sp_Fomc_Previous_Re = "";
   News_Sp_Fomc_Forecast_Re = "";
   News_Sp_Fomc_Count_Down_Re = "";

   News_Sp_Fomc_Title_Up = "";
   News_Sp_Fomc_Date_Up = "";
   News_Sp_Fomc_Currency_Up = "";
   News_Sp_Fomc_Impact_Up = "";
   News_Sp_Fomc_Previous_Up = "";
   News_Sp_Fomc_Forecast_Up = "";
   News_Sp_Fomc_Count_Down_Up = "";


//+------------------------------------------------------------------+
//|          Initialize Speacial NFP News Variables                  |
//+------------------------------------------------------------------+    
   News_Sp_NFP_Title_Re = "";
   News_Sp_NFP_Date_Re = "";
   News_Sp_NFP_Currency_Re = "";
   News_Sp_NFP_Impact_Re = "";
   News_Sp_NFP_Previous_Re = "";
   News_Sp_NFP_Forecast_Re = "";
   News_Sp_NFP_Count_Down_Re = "";

   News_Sp_NFP_Title_Up = "";
   News_Sp_NFP_Date_Up = "";
   News_Sp_NFP_Currency_Up = "";
   News_Sp_NFP_Impact_Up = "";
   News_Sp_NFP_Previous_Up = "";
   News_Sp_NFP_Forecast_Up = "";
   News_Sp_NFP_Count_Down_Up = ""; 
   
   
//+------------------------------------------------------------------+
//|          Set Standard News Object                                |
//+------------------------------------------------------------------+

   ObjectSetString(0,"News_Title_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Date_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Currency_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Impact_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Previous_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Forecast_Re",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Count_Down_Re",OBJPROP_TEXT,"--");

   ObjectSetString(0,"News_Title_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Date_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Currency_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Impact_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Previous_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Forecast_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Count_Down_Up",OBJPROP_TEXT,"--");
   
//+------------------------------------------------------------------+
//|          Set Speacial FOMC News Object                           |
//+------------------------------------------------------------------+ 
   
   ObjectSetString(0,"News_Sp_Fomc_Title_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Date_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Currency_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Impact_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Previous_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Forecast_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Count_Down_Up",OBJPROP_TEXT,"--");
   
   ObjectSetString(0,"News_Sp_Fomc_Title_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Date_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Currency_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Impact_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Previous_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Forecast_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_Fomc_Count_Down_Up",OBJPROP_TEXT,"--");
//+------------------------------------------------------------------+
//|          Set Speacial NFP News  Object                          |
//+------------------------------------------------------------------+
   
   ObjectSetString(0,"News_Sp_NFP_Title_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Date_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Currency_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Impact_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Previous_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Forecast_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Count_Down_Up",OBJPROP_TEXT,"--");
   
   ObjectSetString(0,"News_Sp_NFP_Title_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Date_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Currency_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Impact_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Previous_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Forecast_Up",OBJPROP_TEXT,"--");
   ObjectSetString(0,"News_Sp_NFP_Count_Down_Up",OBJPROP_TEXT,"--");      
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   string News_Title = "";
   string News_Date = "";
   string News_Currency = "";
   string News_Impact = "";
   string News_Previous = "";
   string News_Forecast = "";

  int filehandle=FileOpen(file_name,FILE_SHARE_READ|FILE_CSV|FILE_COMMON,",");
   if(filehandle>=0)
     {
      // Print("------- Open _-------- File");
      while(!FileIsEnding(filehandle))
        {
         News_Title = FileReadString(filehandle);
         News_Date =  FileReadString(filehandle);
         News_Currency = FileReadString(filehandle);
         News_Impact =FileReadString(filehandle);
         News_Previous = FileReadString(filehandle);
         News_Forecast = FileReadString(filehandle);
         if(check_currency(News_Currency)  && check_impact(News_Impact) && check_allowed_keywords(News_Title) && check_not_allowed_keywords(News_Title))
           {
            if(StringToTime(News_Date) <= TimeGMT())
              {
               News_Title_Re = News_Title;
               News_Date_Re = News_Date;
               News_Currency_Re = News_Currency;
               News_Impact_Re = News_Impact;
               News_Previous_Re = News_Previous;
               News_Forecast_Re = News_Forecast;
              }
            else
              {
               News_Title_Up = News_Title;
               News_Date_Up = News_Date;
               News_Currency_Up = News_Currency;
               News_Impact_Up = News_Impact;
               News_Previous_Up = News_Previous;
               News_Forecast_Up = News_Forecast;
               break;
              }
           }
        }
      FileClose(filehandle);
      ObjectSetString(0,"News_Title_Re",OBJPROP_TEXT,News_Title_Re);
      ObjectSetString(0,"News_Date_Re",OBJPROP_TEXT,News_Date_Re);
      ObjectSetString(0,"News_Currency_Re",OBJPROP_TEXT,News_Currency_Re);
      ObjectSetString(0,"News_Impact_Re",OBJPROP_TEXT,News_Impact_Re);
      ObjectSetString(0,"News_Previous_Re",OBJPROP_TEXT,News_Previous_Re);
      ObjectSetString(0,"News_Forecast_Re",OBJPROP_TEXT,News_Forecast_Re);

      ObjectSetString(0,"News_Title_Up",OBJPROP_TEXT,News_Title_Up);
      ObjectSetString(0,"News_Date_Up",OBJPROP_TEXT,News_Date_Up);
      ObjectSetString(0,"News_Currency_Up",OBJPROP_TEXT,News_Currency_Up);
      ObjectSetString(0,"News_Impact_Up",OBJPROP_TEXT,News_Impact_Up);
      ObjectSetString(0,"News_Previous_Up",OBJPROP_TEXT,News_Previous_Up);
      ObjectSetString(0,"News_Forecast_Up",OBJPROP_TEXT,News_Forecast_Up);

     }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
    News_Title = "";
    News_Date = "";
    News_Currency = "";
    News_Impact = "";
    News_Previous = "";
    News_Forecast = "";

   filehandle=FileOpen(file_name,FILE_SHARE_READ|FILE_CSV|FILE_COMMON,",");
   if(filehandle>=0)
     {
      // Print("------- Open _-------- File");
      while(!FileIsEnding(filehandle))
        {
         News_Title = FileReadString(filehandle);
         News_Date =  FileReadString(filehandle);
         News_Currency = FileReadString(filehandle);
         News_Impact =FileReadString(filehandle);
         News_Previous = FileReadString(filehandle);
         News_Forecast = FileReadString(filehandle);
         if(check_currency(News_Currency)  && check_impact(News_Impact) && Is_FOMC(News_Title))
           {
            if(StringToTime(News_Date) <= TimeGMT())
              {
               News_Sp_Fomc_Title_Re = News_Title;
               News_Sp_Fomc_Date_Re = News_Date;
               News_Sp_Fomc_Currency_Re = News_Currency;
               News_Sp_Fomc_Impact_Re = News_Impact;
               News_Sp_Fomc_Previous_Re = News_Previous;
               News_Sp_Fomc_Forecast_Re = News_Forecast;
              }
            else
              {
               News_Sp_Fomc_Title_Up = News_Title;
               News_Sp_Fomc_Date_Up = News_Date;
               News_Sp_Fomc_Currency_Up = News_Currency;
               News_Sp_Fomc_Impact_Up = News_Impact;
               News_Sp_Fomc_Previous_Up = News_Previous;
               News_Sp_Fomc_Forecast_Up = News_Forecast;
               break;
              }
           }
        }
      FileClose(filehandle);
      ObjectSetString(0,"News_Sp_Fomc_Title_Re",OBJPROP_TEXT,News_Sp_Fomc_Title_Re);
      ObjectSetString(0,"News_Sp_Fomc_Date_Re",OBJPROP_TEXT,News_Sp_Fomc_Date_Re);
      ObjectSetString(0,"News_Sp_Fomc_Currency_Re",OBJPROP_TEXT,News_Sp_Fomc_Currency_Re);
      ObjectSetString(0,"News_Sp_Fomc_Impact_Re",OBJPROP_TEXT,News_Sp_Fomc_Impact_Re);
      ObjectSetString(0,"News_Sp_Fomc_Previous_Re",OBJPROP_TEXT,News_Sp_Fomc_Previous_Re);
      ObjectSetString(0,"News_Sp_Fomc_Forecast_Re",OBJPROP_TEXT,News_Sp_Fomc_Forecast_Re);

      ObjectSetString(0,"News_Sp_Fomc_Title_Up",OBJPROP_TEXT,News_Sp_Fomc_Title_Up);
      ObjectSetString(0,"News_Sp_Fomc_Date_Up",OBJPROP_TEXT,News_Sp_Fomc_Date_Up);
      ObjectSetString(0,"News_Sp_Fomc_Currency_Up",OBJPROP_TEXT,News_Sp_Fomc_Currency_Up);
      ObjectSetString(0,"News_Sp_Fomc_Impact_Up",OBJPROP_TEXT,News_Sp_Fomc_Impact_Up);
      ObjectSetString(0,"News_Sp_Fomc_Previous_Up",OBJPROP_TEXT,News_Sp_Fomc_Previous_Up);
      ObjectSetString(0,"News_Sp_Fomc_Forecast_Up",OBJPROP_TEXT,News_Sp_Fomc_Forecast_Up);

     }     
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
    News_Title = "";
    News_Date = "";
    News_Currency = "";
    News_Impact = "";
    News_Previous = "";
    News_Forecast = "";

   filehandle=FileOpen(file_name,FILE_SHARE_READ|FILE_CSV|FILE_COMMON,",");
   if(filehandle>=0)
     {
      // Print("------- Open _-------- File");
      while(!FileIsEnding(filehandle))
        {
         News_Title = FileReadString(filehandle);
         News_Date =  FileReadString(filehandle);
         News_Currency = FileReadString(filehandle);
         News_Impact =FileReadString(filehandle);
         News_Previous = FileReadString(filehandle);
         News_Forecast = FileReadString(filehandle);
         if(check_currency(News_Currency)  && check_impact(News_Impact) && Is_NFP(News_Title))
           {
            if(StringToTime(News_Date) <= TimeGMT())
              {
               News_Sp_NFP_Title_Re = News_Title;
               News_Sp_NFP_Date_Re = News_Date;
               News_Sp_NFP_Currency_Re = News_Currency;
               News_Sp_NFP_Impact_Re = News_Impact;
               News_Sp_NFP_Previous_Re = News_Previous;
               News_Sp_NFP_Forecast_Re = News_Forecast;
              }
            else
              {
               News_Sp_NFP_Title_Up = News_Title;
               News_Sp_NFP_Date_Up = News_Date;
               News_Sp_NFP_Currency_Up = News_Currency;
               News_Sp_NFP_Impact_Up = News_Impact;
               News_Sp_NFP_Previous_Up = News_Previous;
               News_Sp_NFP_Forecast_Up = News_Forecast;
               break;
              }
           }
        }
      FileClose(filehandle);
      ObjectSetString(0,"News_Sp_NFP_Title_Re",OBJPROP_TEXT,News_Sp_NFP_Title_Re);
      ObjectSetString(0,"News_Sp_NFP_Date_Re",OBJPROP_TEXT,News_Sp_NFP_Date_Re);
      ObjectSetString(0,"News_Sp_NFP_Currency_Re",OBJPROP_TEXT,News_Sp_NFP_Currency_Re);
      ObjectSetString(0,"News_Sp_NFP_Impact_Re",OBJPROP_TEXT,News_Sp_NFP_Impact_Re);
      ObjectSetString(0,"News_Sp_NFP_Previous_Re",OBJPROP_TEXT,News_Sp_NFP_Previous_Re);
      ObjectSetString(0,"News_Sp_NFP_Forecast_Re",OBJPROP_TEXT,News_Sp_NFP_Forecast_Re);

      ObjectSetString(0,"News_Sp_NFP_Title_Up",OBJPROP_TEXT,News_Sp_NFP_Title_Up);
      ObjectSetString(0,"News_Sp_NFP_Date_Up",OBJPROP_TEXT,News_Sp_NFP_Date_Up);
      ObjectSetString(0,"News_Sp_NFP_Currency_Up",OBJPROP_TEXT,News_Sp_NFP_Currency_Up);
      ObjectSetString(0,"News_Sp_NFP_Impact_Up",OBJPROP_TEXT,News_Sp_NFP_Impact_Up);
      ObjectSetString(0,"News_Sp_NFP_Previous_Up",OBJPROP_TEXT,News_Sp_NFP_Previous_Up);
      ObjectSetString(0,"News_Sp_NFP_Forecast_Up",OBJPROP_TEXT,News_Sp_NFP_Forecast_Up);

     }
          
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
datetime fun(string s)
  {
   string year = StringSubstr(s,0,4);
   string month = StringSubstr(s,5,2);
   string day = StringSubstr(s,8,2);
   string hour = StringSubstr(s,11,2);
   string minute = StringSubstr(s,14,2);
   string second = StringSubstr(s,17,2);
   string offset_hour = StringSubstr(s,20,2);
   string offset_minute = StringSubstr(s,23,2);
   string offset_sign = StringSubstr(s,19,1);
   datetime time_1 = StringToTime(year+"."+month+"."+day+" "+hour+":"+minute+":"+second);
   int tot_offset_secnds = int((StringToInteger(offset_hour)*3600) + (StringToInteger(offset_minute)*60));
   if(offset_sign=="-")
     {
      time_1 = time_1+tot_offset_secnds;
     }
   else
     {
      time_1 = time_1-tot_offset_secnds;
     }
   return time_1;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool CheckSymbol(string sym)
  {
   return (StringFind(News_Symbols,sym)>=0);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_currency(string cur)
  {
   if(CheckSymbol("AUD") && cur=="AUD")
      return true;
   if(CheckSymbol("CAD") && cur=="CAD")
      return true;
   if(CheckSymbol("CHF") && cur=="CHF")
      return true;
   if(CheckSymbol("CNY") && cur=="CNY")
      return true;
   if(CheckSymbol("EUR") && cur=="EUR")
      return true;
   if(CheckSymbol("GBP") && cur=="GBP")
      return true;
   if(CheckSymbol("JPY") && cur=="JPY")
      return true;
   if(CheckSymbol("NZD") && cur=="NZD")
      return true;
   if(CheckSymbol("USD") && cur=="USD")
      return true;
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_impact(string imp)
  {
   if(High_Impact == true && imp=="High")
      return true;
   if(Medium_Impact == true && imp=="Medium")
      return true;
   if(Low_Impact == true && imp=="Low")
      return true;
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_allowed_keywords(string news)
  {
   if(!Use_Allow_KeyWords || Allowed_KeyWords == "")
     {
      return true;
     }
   string key_words[];
   StringSplit(Allowed_KeyWords,u_sep,key_words);
   for(int i = 0; i<ArraySize(key_words); i++)
     {
      if(StringFind(news,key_words[i],0)>=0)
        {
         return true;
        }
     }
   return false;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  
bool Is_FOMC(string news)
{
   string key_words[];
   StringSplit(Special_Events_FOMC_KeyWords,u_sep,key_words);
   for(int i = 0; i<ArraySize(key_words); i++)
     {
      if(StringFind(news,key_words[i],0)>=0)
        {
         return true;
        }
     }
   return false;
} 

bool Is_NFP(string news)
{
   string key_words[];
   StringSplit(Special_Events_NFP_KeyWords,u_sep,key_words);
   for(int i = 0; i<ArraySize(key_words); i++)
     {
      if(StringFind(news,key_words[i],0)>=0)
        {
         return true;
        }
     }
   return false;
} 
  
  
  
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool check_not_allowed_keywords(string news)
  {
   if(!Use_DoNot_Allow_KeyWords || DoNot_Allowed_KeyWords == "")
     {
      return true;
     }
   string key_words[];
   StringSplit(DoNot_Allowed_KeyWords,u_sep,key_words);
   for(int i = 0; i<ArraySize(key_words); i++)
     {
      if(StringFind(news,key_words[i],0)>=0)
        {
         return false;
        }
     }
   return true;
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string SecondsToTimeString(int totalSeconds)
  {
   int days = totalSeconds / 86400;
   int hours = (totalSeconds % 86400) / 3600;
   int minutes = (totalSeconds % 3600) / 60;
   int seconds = totalSeconds % 60;

   string formattedTime = IntegerToString(days) + " : " +
                          IntegerToString(hours) + " : " +
                          IntegerToString(minutes) + " : " +
                          IntegerToString(seconds);

   return formattedTime;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void News_File_Writes()
  {
   int filehandle=FileOpen(file_name,FILE_WRITE|FILE_CSV|FILE_COMMON,",");
   if(filehandle>=0)
     {
      string baseUrl = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
      string headers = "";
      string requestURL = "";
      string requestHeaders = "";
      char resultData [];
      char posData [];
      int timeout= 2000;
      int response = WebRequest("GET", baseUrl, headers, timeout, posData, resultData, requestHeaders);
      string resultMessage = CharArrayToString(resultData);
      string jsonString = CharArrayToString(resultData);
      // Print(" resultMessage "+resultMessage);

      Print("--------- requestHeaders  ",requestHeaders);
      Print("--------- response  ",response);
      if(response == 200)
        {
         CJAVal js(NULL,jtUNDEF);
         js.Deserialize(jsonString);
         for(int i=0; i<ArraySize(js.m_e) ; i++)
           {
            FileWrite(filehandle,
                      js[i]["title"].ToStr(),
                      TimeToString(fun(js[i]["date"].ToStr()),TIME_DATE | TIME_MINUTES | TIME_SECONDS),
                      js[i]["country"].ToStr(),
                      js[i]["impact"].ToStr(),
                      js[i]["forecast"].ToStr(),
                      js[i]["previous"].ToStr()
                     );
           }
           FileClose(filehandle);
        }
      else
      {
       FileClose(filehandle);
       FileDelete(file_name,FILE_COMMON);
      }  
     }

  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool EditCreate(const string _name,const int x,const int y,const int width,const int height,const string text,const string font,const int font_size,const color back_clr)
  {
   const long             chart_ID=0;
   const int              sub_window=0;
   const ENUM_ALIGN_MODE  align=ALIGN_CENTER;
   const bool             read_only=true;
   const ENUM_BASE_CORNER corner=CORNER_LEFT_LOWER;
   const color            clr=clrWhite;
   const color            border_clr=clrBlack;
   const bool             back=false;
   const bool             selection=false;
   const bool             hidden=true;
   const long             z_order=0;
   ObjectDelete(chart_ID,_name);
   ObjectCreate(chart_ID,_name,OBJ_EDIT,sub_window,0,0);
   ObjectSetInteger(chart_ID,_name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(chart_ID,_name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(chart_ID,_name,OBJPROP_XSIZE,width);
   ObjectSetInteger(chart_ID,_name,OBJPROP_YSIZE,height);
   ObjectSetString(chart_ID,_name,OBJPROP_TEXT,text);
   ObjectSetString(chart_ID,_name,OBJPROP_FONT,font);
   ObjectSetInteger(chart_ID,_name,OBJPROP_FONTSIZE,font_size);
   ObjectSetInteger(chart_ID,_name,OBJPROP_ALIGN,align);
   ObjectSetInteger(chart_ID,_name,OBJPROP_READONLY,read_only);
   ObjectSetInteger(chart_ID,_name,OBJPROP_CORNER,corner);
   ObjectSetInteger(chart_ID,_name,OBJPROP_COLOR,clr);
   ObjectSetInteger(chart_ID,_name,OBJPROP_BGCOLOR,back_clr);
   ObjectSetInteger(chart_ID,_name,OBJPROP_BORDER_COLOR,border_clr);
   ObjectSetInteger(chart_ID,_name,OBJPROP_BACK,back);
   ObjectSetInteger(chart_ID,_name,OBJPROP_SELECTABLE,selection);
   ObjectSetInteger(chart_ID,_name,OBJPROP_SELECTED,selection);
   ObjectSetInteger(chart_ID,_name,OBJPROP_HIDDEN,hidden);
   ObjectSetInteger(chart_ID,_name,OBJPROP_ZORDER,z_order);
   return(true);
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string News_Title_Re = "";
string News_Date_Re = "";
string News_Currency_Re = "";
string News_Impact_Re = "";
string News_Previous_Re = "";
string News_Forecast_Re = "";
string News_Count_Down_Re = "";

string News_Title_Up = "";
string News_Date_Up = "";
string News_Currency_Up = "";
string News_Impact_Up = "";
string News_Previous_Up = "";
string News_Forecast_Up = "";
string News_Count_Down_Up = "";

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string   News_Sp_Fomc_Title_Re = "";
string   News_Sp_Fomc_Date_Re = "";
string   News_Sp_Fomc_Currency_Re = "";
string   News_Sp_Fomc_Impact_Re = "";
string   News_Sp_Fomc_Previous_Re = "";
string   News_Sp_Fomc_Forecast_Re = "";
string   News_Sp_Fomc_Count_Down_Re = "";

string   News_Sp_Fomc_Title_Up = "";
string   News_Sp_Fomc_Date_Up = "";
string   News_Sp_Fomc_Currency_Up = "";
string   News_Sp_Fomc_Impact_Up = "";
string   News_Sp_Fomc_Previous_Up = "";
string   News_Sp_Fomc_Forecast_Up = "";
string   News_Sp_Fomc_Count_Down_Up = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
string   News_Sp_NFP_Title_Re = "";
string   News_Sp_NFP_Date_Re = "";
string   News_Sp_NFP_Currency_Re = "";
string   News_Sp_NFP_Impact_Re = "";
string   News_Sp_NFP_Previous_Re = "";
string   News_Sp_NFP_Forecast_Re = "";
string   News_Sp_NFP_Count_Down_Re = "";

string   News_Sp_NFP_Title_Up = "";
string   News_Sp_NFP_Date_Up = "";
string   News_Sp_NFP_Currency_Up = "";
string   News_Sp_NFP_Impact_Up = "";
string   News_Sp_NFP_Previous_Up = "";
string   News_Sp_NFP_Forecast_Up = "";
string   News_Sp_NFP_Count_Down_Up = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   




datetime tmr = 0;
void NewsInintialization()
  {
   if(UseNewsFilter && !MQLInfoInteger(MQL_TESTER))
     {
      tmr = 0;
      tm_h = 0;


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
      News_Title_Re = "";
      News_Date_Re = "";
      News_Currency_Re = "";
      News_Impact_Re = "";
      News_Previous_Re = "";
      News_Forecast_Re = "";
      News_Count_Down_Re = "";

      News_Title_Up = "";
      News_Date_Up = "";
      News_Currency_Up = "";
      News_Impact_Up = "";
      News_Previous_Up = "";
      News_Forecast_Up = "";
      News_Count_Down_Up = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//|          Initialize Speacial FOMC News Variables                 |
//+------------------------------------------------------------------+  
   News_Sp_Fomc_Title_Re = "";
   News_Sp_Fomc_Date_Re = "";
   News_Sp_Fomc_Currency_Re = "";
   News_Sp_Fomc_Impact_Re = "";
   News_Sp_Fomc_Previous_Re = "";
   News_Sp_Fomc_Forecast_Re = "";
   News_Sp_Fomc_Count_Down_Re = "";

   News_Sp_Fomc_Title_Up = "";
   News_Sp_Fomc_Date_Up = "";
   News_Sp_Fomc_Currency_Up = "";
   News_Sp_Fomc_Impact_Up = "";
   News_Sp_Fomc_Previous_Up = "";
   News_Sp_Fomc_Forecast_Up = "";
   News_Sp_Fomc_Count_Down_Up = "";


//+------------------------------------------------------------------+
//|          Initialize Speacial NFP News Variables                  |
//+------------------------------------------------------------------+    
   News_Sp_NFP_Title_Re = "";
   News_Sp_NFP_Date_Re = "";
   News_Sp_NFP_Currency_Re = "";
   News_Sp_NFP_Impact_Re = "";
   News_Sp_NFP_Previous_Re = "";
   News_Sp_NFP_Forecast_Re = "";
   News_Sp_NFP_Count_Down_Re = "";

   News_Sp_NFP_Title_Up = "";
   News_Sp_NFP_Date_Up = "";
   News_Sp_NFP_Currency_Up = "";
   News_Sp_NFP_Impact_Up = "";
   News_Sp_NFP_Previous_Up = "";
   News_Sp_NFP_Forecast_Up = "";
   News_Sp_NFP_Count_Down_Up = "";
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
   ObjectsDeleteAll(0,"News");

      int xx = 0;
      int yy = 140;
      int dd = 20;
      int head_font  = 8;
      int txt_font = 7;
      string head_font_name = "Georgia Bold";
      string txt_font_name = "Georgia";
      if(Display_News)
        {
         // News_Title,News_Date,News_Currency,News_Impact,News_Previous,News_Forecast,News_Count
         //----------------- Heading
         EditCreate("News_Main",xx,yy+20,920,20,"Time GMT    "+TimeToString(TimeGMT(),TIME_DATE|TIME_MINUTES|TIME_SECONDS),head_font_name,8,clrOliveDrab);
         EditCreate("News_Title",xx,yy,200,20,"Title",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Date",xx+200,yy,200,20,"Date/Time",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Currency",xx+2*200,yy,80,20,"Currency",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Impact",xx+2*200+80,yy,80,20,"Impact",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Previous",xx+2*200+2*80,yy,80,20,"Previous",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Forecast",xx+2*200+3*80,yy,80,20,"Forecast",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Count_Down",xx+2*200+4*80,yy,100,20,"D:H:M:S",head_font_name,head_font,clrOliveDrab);
         EditCreate("News_Type",xx+2*200+5*80+20,yy,100,20,"News Type",head_font_name,head_font,clrOliveDrab);
         //------------------ Recent

         EditCreate("News_Title_Re",xx,yy-dd,200,20,"Title",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Date_Re",xx+200,yy-dd,200,20,"Date/Time",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Currency_Re",xx+2*200,yy-dd,80,20,"Currency",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Impact_Re",xx+2*200+80,yy-dd,80,20,"Impact",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Previous_Re",xx+2*200+2*80,yy-dd,80,20,"Previous",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Forecast_Re",xx+2*200+3*80,yy-dd,80,20,"Forecast",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Count_Down_Re",xx+2*200+4*80,yy-dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Type_Stan_Re",xx+2*200+5*80+20,yy-dd,100,20,"Standard(Pre)",txt_font_name,txt_font,clrBlueViolet);

         //------------------ UpComing

         EditCreate("News_Title_Up",xx,yy-2*dd,200,20,"Title",txt_font_name,txt_font,clrRed);
         EditCreate("News_Date_Up",xx+200,yy-2*dd,200,20,"Date/Time",txt_font_name,txt_font,clrRed);
         EditCreate("News_Currency_Up",xx+2*200,yy-2*dd,80,20,"Currency",txt_font_name,txt_font,clrRed);
         EditCreate("News_Impact_Up",xx+2*200+80,yy-2*dd,80,20,"Impact",txt_font_name,txt_font,clrRed);
         EditCreate("News_Previous_Up",xx+2*200+2*80,yy-2*dd,80,20,"Previous",txt_font_name,txt_font,clrRed);
         EditCreate("News_Forecast_Up",xx+2*200+3*80,yy-2*dd,80,20,"Forecast",txt_font_name,txt_font,clrRed);
         EditCreate("News_Count_Down_Up",xx+2*200+4*80,yy-2*dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrRed);
         EditCreate("News_Type_Stan_Up",xx+2*200+5*80+20,yy-2*dd,100,20,"Standard(UP)",txt_font_name,txt_font,clrRed);
         
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+         
         EditCreate("News_Sp_Fomc_Title_Re",xx,yy-3*dd,200,20,"Title",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Date_Re",xx+200,yy-3*dd,200,20,"Date/Time",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Currency_Re",xx+2*200,yy-3*dd,80,20,"Currency",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Impact_Re",xx+2*200+80,yy-3*dd,80,20,"Impact",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Previous_Re",xx+2*200+2*80,yy-3*dd,80,20,"Previous",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Forecast_Re",xx+2*200+3*80,yy-3*dd,80,20,"Forecast",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_Fomc_Count_Down_Re",xx+2*200+4*80,yy-3*dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrBlueViolet);         
         EditCreate("News_Sp_Fomc_Type_Re",xx+2*200+5*80+20,yy-3*dd,100,20,"FOMC(Pre)",txt_font_name,txt_font,clrBlueViolet);
         
         
         EditCreate("News_Sp_Fomc_Title_Up",xx,yy-4*dd,200,20,"Title",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Date_Up",xx+200,yy-4*dd,200,20,"Date/Time",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Currency_Up",xx+2*200,yy-4*dd,80,20,"Currency",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Impact_Up",xx+2*200+80,yy-4*dd,80,20,"Impact",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Previous_Up",xx+2*200+2*80,yy-4*dd,80,20,"Previous",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Forecast_Up",xx+2*200+3*80,yy-4*dd,80,20,"Forecast",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Count_Down_Up",xx+2*200+4*80,yy-4*dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_Fomc_Type_Up",xx+2*200+5*80+20,yy-4*dd,100,20,"FOMC(Up)",txt_font_name,txt_font,clrRed);

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+  

         EditCreate("News_Sp_NFP_Title_Re",xx,yy-5*dd,200,20,"Title",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Date_Re",xx+200,yy-5*dd,200,20,"Date/Time",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Currency_Re",xx+2*200,yy-5*dd,80,20,"Currency",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Impact_Re",xx+2*200+80,yy-5*dd,80,20,"Impact",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Previous_Re",xx+2*200+2*80,yy-5*dd,80,20,"Previous",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Forecast_Re",xx+2*200+3*80,yy-5*dd,80,20,"Forecast",txt_font_name,txt_font,clrBlueViolet);
         EditCreate("News_Sp_NFP_Count_Down_Re",xx+2*200+4*80,yy-5*dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrBlueViolet);       
         EditCreate("News_Sp_NFP_Type_Stan_Re",xx+2*200+5*80+20,yy-5*dd,100,20,"NFP(Pre)",txt_font_name,txt_font,clrBlueViolet);


         EditCreate("News_Sp_NFP_Title_Up",xx,yy-6*dd,200,20,"Title",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Date_Up",xx+200,yy-6*dd,200,20,"Date/Time",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Currency_Up",xx+2*200,yy-6*dd,80,20,"Currency",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Impact_Up",xx+2*200+80,yy-6*dd,80,20,"Impact",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Previous_Up",xx+2*200+2*80,yy-6*dd,80,20,"Previous",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Forecast_Up",xx+2*200+3*80,yy-6*dd,80,20,"Forecast",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Count_Down_Up",xx+2*200+4*80,yy-6*dd,100,20,"D:H:M:S",txt_font_name,txt_font,clrRed);
         EditCreate("News_Sp_NFP_Type_Stan_Up",xx+2*200+5*80+20,yy-6*dd,100,20,"NFP(UP)",txt_font_name,txt_font,clrRed);
         
        }
      EventSetTimer(1);
     }
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int TimeDay(datetime date)
  {
   MqlDateTime tm;
   TimeToStruct(date,tm);
   return(tm.day);
  }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void Write_News_On_File()
  {
   datetime file_modify_date = datetime(FileGetInteger(file_name,FILE_MODIFY_DATE,true));
   bool cond_1 = (FileIsExist(file_name,FILE_COMMON) == false);
   bool cond_2 = (TimeDay(file_modify_date) != TimeDay(TimeCurrent()));
//Print("   Enter ");
   if(cond_1 || cond_2)
     {
      Print("   FILE_MODIFY_DATE  ",file_modify_date);
      Print(" FILE_CREATE_DATE    ",datetime(FileGetInteger(file_name,FILE_CREATE_DATE,true)));
      //Print(TimeDayOfWeek(file_modify_date),"   ",DayOfWeek());
      Print(cond_1,"      ---------- Create File    ----------",cond_2);
      Print(" ------------- Writing File @ ------> ",TimeCurrent());
      News_File_Writes();
     }
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool standard_red_news = false;
bool special_fomc_red_news = false;
bool speacial_nfp_red_news = false;
void check_news()
  {
   
   standard_red_news = false;
   special_fomc_red_news = false;
   speacial_nfp_red_news = false;
   if(MQLInfoInteger(MQL_TESTER))
   {
    return;
   }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   if(Enable_Red_News_Filter)
   {
      if(
         (News_Title_Re!="" && TimeGMT() <= (StringToTime(News_Date_Re) + Block_Trade_Minutes_After)) ||
         (News_Title_Up!="" && TimeGMT() >= (StringToTime(News_Date_Up) - Block_Trade_Minutes_Before))
      )
      {
         standard_red_news = true;
      }    
   }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+   
   if(Enable_Special_Event_Close)
   {
     // Print("  Enter ",News_Sp_Fomc_Title_Up);
      if(News_Sp_Fomc_Title_Up!="" && TimeGMT() >= (StringToTime(News_Sp_Fomc_Date_Up) - Close_Trades_Minutes_Before_FOMC))
         {
          if(Tot_TradesAll())
          {
            Print("   Closing All On FOMC ",News_Sp_Fomc_Title_Up);
            CloseAllActvPending();
          }
          special_fomc_red_news = true;
         }
         if(Block_New_Trades_Until_End_Of_Day_FOMC  && News_Sp_Fomc_Title_Re!="" &&  StringToTime(TimeToString(StringToTime(News_Sp_Fomc_Date_Re),TIME_DATE)) == StringToTime(TimeToString(TimeGMT(),TIME_DATE)))
         {
          special_fomc_red_news = true;
         }
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+

      if(News_Sp_NFP_Title_Up!="" && TimeGMT() >= (StringToTime(News_Sp_NFP_Date_Up) - Close_Trades_Minutes_Before_NFP))
         {
          if(Tot_TradesAll())
          {
            Print("   Closing All On NFP ",News_Sp_NFP_Title_Up);
            CloseAllActvPending();
          }
          speacial_nfp_red_news = true;
         }
         if(Block_New_Trades_Until_End_Of_Day_NFP  && News_Sp_NFP_Title_Re!="" &&  StringToTime(TimeToString(StringToTime(News_Sp_NFP_Date_Re),TIME_DATE)) == StringToTime(TimeToString(TimeGMT(),TIME_DATE)))
         {
          speacial_nfp_red_news = true;
         }              
   }

  }



//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
bool LabelCreate(const string name,const int x,const int y,const string text,const int font_size,const color clr)
  {
   const long              chart_ID=0;
   const int               sub_window=0;
   const ENUM_BASE_CORNER  corner=CORNER_LEFT_UPPER;
   const string            font="Arial";
   const double            angle=0.0;
   const ENUM_ANCHOR_POINT anchor=ANCHOR_LEFT_UPPER;
   const bool              back=false;
   const bool              selection=false;
   const bool              hidden=true;
   const long              z_order=0;
   ObjectDelete(chart_ID,name);
   ObjectCreate(chart_ID,name,OBJ_LABEL,sub_window,0,0);
   ObjectSetInteger(chart_ID,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(chart_ID,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(chart_ID,name,OBJPROP_CORNER,corner);
   ObjectSetString(chart_ID,name,OBJPROP_TEXT,text);
   ObjectSetString(chart_ID,name,OBJPROP_FONT,font);
   ObjectSetInteger(chart_ID,name,OBJPROP_FONTSIZE,font_size);
   ObjectSetDouble(chart_ID,name,OBJPROP_ANGLE,angle);
   ObjectSetInteger(chart_ID,name,OBJPROP_ANCHOR,anchor);
   ObjectSetInteger(chart_ID,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(chart_ID,name,OBJPROP_BACK,back);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTABLE,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_SELECTED,selection);
   ObjectSetInteger(chart_ID,name,OBJPROP_HIDDEN,hidden);
   ObjectSetInteger(chart_ID,name,OBJPROP_ZORDER,z_order);
   return(true);
  }


//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
int TotalTrades()
  {
   int cnt = 0;
   for(int i =OrdersTotal()-1 ; i>=0 ; i--)
     {
      if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
        {
        // if((OrderSymbol() == Symbol()) && (OrderType() == OP_BUY || OrderType() == OP_SELL || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT || OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP) && (OrderMagicNumber() == Magic_Number))
           {
            cnt++;
           }
        }
     }
   return cnt;
  }

//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
void CloseAllActvPending()
  {
   for(int i =OrdersTotal()-1 ; i>=0 ; i--)
     {
      if((OrderSelect(i, SELECT_BY_POS,MODE_TRADES)==true))
        {
        // if((OrderSymbol() == Symbol())  && (OrderMagicNumber() == Magic_Number))
           {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL)
            OrderClose(OrderTicket(),OrderLots(),OrderClosePrice(),50,clrNONE,NULL);
            if(OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP || OrderType() == OP_BUYLIMIT || OrderType() == OP_SELLLIMIT)
            OrderDelete(OrderTicket());
           }
        }
     }
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
bool Check_Price_Range_Broker(int trd_typ,double open_price)
{ 
  int digits = SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
  double points = SymbolInfoDouble(_Symbol,SYMBOL_POINT);
  if(Use_ExtremeRange_Restriction)
  {
    double highest = iHigh(_Symbol,ExtremeRange_TF,1); 
    double lowest =  iLow(_Symbol,ExtremeRange_TF,1); 
    for(int i = 1; i<=ExtremeRange_Candle_Count; i++)
    {
      if(iHigh(_Symbol,ExtremeRange_TF,i)>highest)
      {
       highest = iHigh(_Symbol,ExtremeRange_TF,i);
      }
      if(iLow(_Symbol,ExtremeRange_TF,i)<lowest)
      {
       lowest = iLow(_Symbol,ExtremeRange_TF,i);
      }
    } 
    double buf_hi = NormalizeDouble(highest*(1-ExtremeRange_Buffer_Percent/100),digits);
    double buf_lo = NormalizeDouble(lowest*(1+ExtremeRange_Buffer_Percent/100),digits);
    if(trd_typ == OP_BUY && open_price<=buf_lo)
    {
        string log_msg =   "[EXTREME_RANGE_BLOCK] Trade Blocked" 
                           +"Direction: Buy" 
                           +"Entry Price: "+open_price  
                           +"Lowest Low ("+ExtremeRange_Candle_Count+" x "+EnumToString(ExtremeRange_TF)+"): "+lowest  
                           +"Buffer Price: "+ExtremeRange_Buffer_Percent+"% "+buf_lo
                           +"Reason: Entry below range threshold (possible breakdown)";
                           
       
        if(Journal_ExtremeRange_Block)Print(log_msg); 
        return false;
    } 
    if(trd_typ == OP_SELL && open_price>=buf_hi)
    {
        string log_msg =   "[EXTREME_RANGE_BLOCK] Trade Blocked" 
                           +"Direction: Sell" 
                           +"Entry Price: "+open_price 
                           +"Lowest Low ("+ExtremeRange_Candle_Count+" x "+EnumToString(ExtremeRange_TF)+"): "+highest 
                           +"Buffer Price: "+ExtremeRange_Buffer_Percent+"% "+buf_hi
                           +"Reason: Entry above range threshold (possible breakdown)";
                           
       
        if(Journal_ExtremeRange_Block)Print(log_msg);
        return false;
    }       
  }  
  return true;
}  