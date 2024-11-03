from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5
from pushover import Pushover

po = Pushover("abkcrum6gvhtukc6y92eqexgrwes1a")
po.user("uu9g36cgw2kvhawuxxn7fb3fe85hib")

#IC Markets

mt_account1 = None
mt_pass1 = None
mt_server1 = None
terminal_path1 = None




###########################################################################

logged_trades = []
double_logged_trades = []

range_crossed = False

timestamp = 0
open = 1
high = 2
low = 3
close = 4
imbalance_poi_pos = []
imbalance_poi_neg = []

ticket = 0
#time = 1
lot_sizerr = 9
entry_price = 10
stop_loss = 11
take_profit = 12
current_profit = 17
current_symbol = 16


permitted_positions = []
maximum_trades = 6
rates = None

number_of_candles = 350
pipp = 0
is_buy = True
utc_from = datetime.now() + timedelta(hours=200) 

symbol_iteration = 1
class MaxRetriesExceeded(Exception):
    pass

def send_notification(title, message):
    msg = po.msg(message)
    msg.set('title', title)
    po.send(msg)

def retryable_initialize(max_retries, delay_seconds, terminal_path, account_number, account_pass, account_server):
    for attempt in range(1, max_retries + 1):
        if mt5.initialize(terminal_path):
            authorized = mt5.login(login=account_number, password=account_pass, server=account_server)
            #time.sleep(delay_seconds)
            if not authorized:
                print("Failed to connect at account #{}, error code: {}".format(account_number, mt5.last_error()))
            return True  # If successful, exit the loop and return True
        else:
            print(f"Attempt {attempt} failed to initialize, account: {account_number}, error code: {mt5.last_error()}")
            #ime.sleep(delay_seconds)  # Wait for the specified time before the next attempt

    raise MaxRetriesExceeded(f"Max retries ({max_retries}) reached. Initialization failed.")

def reverse_type(type):
    if type == mt5.ORDER_TYPE_BUY:
        return mt5.ORDER_TYPE_SELL
    elif type == mt5.ORDER_TYPE_SELL:
        return mt5.ORDER_TYPE_BUY

opened_positions = []


SCRIPT_VERSION = 'RISK MANAGEMENT'
SCRIPT_MAGIC = 20000

def getprofit():
    current_profit = 0
    current_profit = mt5.positions_get()
    if current_profit==None:
        print("No Open Positions", ", error code={}".format(mt5.last_error()))
    elif len(current_profit)>0:  
        profit = 0 
        for profits in current_profit:
            profit += profits[15]
            #if profits[6] == SCRIPT_MAGIC:
            #    profit += profits[15]
        return profit
def getprofit_single(tick):
    current_profit = 0
    current_profit = mt5.positions_get(ticket=tick)
    if current_profit==None:
        print("No Open Positions", ", error code={}".format(mt5.last_error()))
    elif len(current_profit)>0:  
        profit = 0 
        for profits in current_profit:
            profit += profits[15]
            #if profits[6] == SCRIPT_MAGIC:
            #    profit += profits[15]
        return profit

def open_trade(symbol, lot_size=0.1, stop_loss=100, take_profit=100, deviation=20, b_s = None):
    global pipp, is_buy
    # Initialize MetaTrader 5
    is_buy = b_s
    print(f'IS IT A BUY?: {is_buy}')
    #try:
    #    if not retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2):
    #        print("Initialization failed even after retries.")
    #        #send_notification('Script Stopped', 'Initialisation failed')
    #    else:
    #        print("Initialization successful!")
    #except MaxRetriesExceeded as e:
    #    print(e)
    # Check if the symbol is available in MarketWatch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot call order_check()")
        mt5.shutdown()
        return
    # Add the symbol if it is not visible
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            mt5.shutdown()
            return
    # Prepare the trading request
    price = mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        #"sl": (price - price) + stop_loss if is_buy else (price - price) + stop_loss,
        #"tp": (price - price) + take_profit if is_buy else (price - price) + take_profit,
        "deviation": deviation,
        "magic": SCRIPT_MAGIC,
        "comment": SCRIPT_VERSION,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    # Send the trading request
    result = mt5.order_send(request)
    
    # Check the execution result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field, value in result_dict.items():
            print(f"   {field}={value}")
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_field, tradereq_value in traderequest_dict.items():
                    print(f"       traderequest: {tradereq_field}={tradereq_value}")
        print("shutdown() and quit")
        mt5.shutdown()
        return
    else:
        sl_increment = (((price - price) + take_profit if is_buy else (price - price) + take_profit) - price)/4
        opened_positions.append([result.order, price, price+sl_increment, price+(sl_increment*2), price+(sl_increment*3)])
    
    if is_buy:
        
        print("Opened BUY position with POSITION_TICKET={}".format(result.order))
        #send_notification("BUY Position opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        pipp = result.price
        return (result.order)
    else: 
        
        print("Opened SELL position with POSITION_TICKET={}".format(result.order))
        #send_notification("SELL Position Opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        pipp = result.price
        return (result.order)

def modify_trade(symbol = None, deviation=20, pos_ticket = None, new_stop = None, new_take = None):
    global pipp
    # Initialize MetaTrader 5
    
    # Check if the symbol is available in MarketWatch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot call order_check()")
        mt5.shutdown()
        return
    # Add the symbol if it is not visible
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            mt5.shutdown()
            return
    # Prepare the trading request
    price = mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": pos_ticket,
        "symbol": symbol,
        "sl": new_stop,
        "tp": new_take,
        "deviation": deviation,
        "magic": SCRIPT_MAGIC,
    }
    # Send the trading request
    result = mt5.order_send(request)
    
    # Check the execution result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field, value in result_dict.items():
            print(f"   {field}={value}")
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_field, tradereq_value in traderequest_dict.items():
                    print(f"       traderequest: {tradereq_field}={tradereq_value}")
        print("shutdown() and quit")
        mt5.shutdown()
        return
    else:
        sl_increment = (((price - price) + take_profit if is_buy else (price - price) + take_profit) - price)/4
        opened_positions.append([result.order, price, price+sl_increment, price+(sl_increment*2), price+(sl_increment*3)])
    
    if is_buy:
        print("Opened BUY position with POSITION_TICKET={}".format(result.order))
        
        #send_notification("BUY Position opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        
    else:
        print("Opened SELL position with POSITION_TICKET={}".format(result.order))
        
        #send_notification("SELL Position Opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        

def close_trade(ticket=None, symbol=None, lot=None, typee=None, message = None):
    # Get position details
    price = mt5.symbol_info_tick(symbol).bid

    # Create close request
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": reverse_type(typee),
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "trade copier",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send close request
    close_result = mt5.order_send(close_request)

    # Check the execution result
    text =("Close position #{}: sell {} {} lots at {} ".format(ticket, symbol, lot, price))
    print(text)
    if message is not None:
        send_notification('MAX P/L HIT', text)
    if close_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Order send failed, retcode={}".format(close_result.retcode))
        print("Result:", close_result)
    

# Assuming max_position_risk is already defined and holds the maximum drawdown risk
def close_positions_in_drawdown(max_position_risk):
    open_positions = mt5.positions_get()  # Fetch all open positions

    if open_positions is None:
        print("No open positions, error code: {}".format(mt5.last_error()))
        return
    
    for position in open_positions:
        print(position)
        # Extract relevant information about the position
        position_ticket = position[0]  # Ticket number
        position_symbol = position[16]  # Symbol of the position
        position_profit = position[15]    # Current profit of the position
        position_open_price = position[10] # Opening price of the position

        # Calculate drawdown (negative profit)
        drawdown = position_profit

        # Check if the drawdown exceeds the max position risk
        print(f'drawdown: {drawdown}')
        print(f'max pos risk: {-max_position_risk}')
        if drawdown <= -max_position_risk:
            # Close the position
            print(f"Closing position {position_ticket} on {position_symbol} due to drawdown of {drawdown}")
            close_trade(position_ticket, position_symbol, position[9], position[5], message='Position closed due to drawdown')

def round_to_nearest_0_2(number):
    return round(number * 5) / 5

def check_closed_positions():
    global logged_trades, double_logged_trades
    
    for trade_id, sl, tp in double_logged_trades:
        retryable_initialize(3, 5, terminal_path1, mt_account1, mt_pass1, mt_server1)
        trade = mt5.positions_get(ticket=trade_id)

        if not trade:
            print(f"Position closed: {trade_id}")
            position_symbol = mt5.history_orders_get(ticket=trade_id)
            print(position_symbol)
                        
            text = f"🚨Position Closed🚨\n🚨EXIT TRADE🚨\n \nID: {trade_id}\nSymbol: {position_symbol[0][21]}\nClosing Price: {position_symbol[0][19]}"
            #client.loop.run_until_complete(client.send_message(chat_id, text))

            # Update your logic for max_daily_loss and total_position_risk if needed
            print(text)
            # Remove the closed position from the double_logged_trades list
            double_logged_trades = [(t_id, t_sl, t_tp) for t_id, t_sl, t_tp in double_logged_trades if t_id != trade_id]