from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5

#IC Markets

mt_account1 = None
mt_pass1 = None
mt_server1 = None
terminal_path1 = None

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


opened_positions = []
SCRIPT_VERSION = 'RISK MANAGEMENT'
SCRIPT_MAGIC = 20000
number_of_candles = 350
pipp = 0
is_buy = True
utc_from = datetime.now() + timedelta(hours=200) 

symbol_iteration = 1
class MaxRetriesExceeded(Exception):
    pass

def retryable_initialize(max_retries, delay_seconds, terminal_path, account_number, account_pass, account_server):
    
    """
    Attempts to initialize a MetaTrader 5 (MT5) terminal and log in to a trading account, retrying up to a specified number of times.

    Parameters:
    - max_retries (int): The maximum number of initialization attempts allowed.
    - delay_seconds (int): The delay in seconds between each retry attempt. (Currently commented out in the function.)
    - terminal_path (str): The file path to the MT5 terminal executable.
    - account_number (int): The trading account number to log in.
    - account_pass (str): The password for the trading account.
    - account_server (str): The server address associated with the trading account.

    Returns:
    - bool: Returns True if the initialization and login are successful.

    Raises:
    - MaxRetriesExceeded: If all retry attempts fail, raises an exception indicating the maximum retries have been exceeded.
    """
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
    """
    Reverses the given order type in MetaTrader 5 (MT5).

    Parameters:
    - type (int): The order type to reverse. Expected values are:
        - mt5.ORDER_TYPE_BUY: Represents a buy order.
        - mt5.ORDER_TYPE_SELL: Represents a sell order.

    Returns:
    - int: The reversed order type:
        - If input is mt5.ORDER_TYPE_BUY, returns mt5.ORDER_TYPE_SELL.
        - If input is mt5.ORDER_TYPE_SELL, returns mt5.ORDER_TYPE_BUY.

    Note:
    - If the input does not match either mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL, the function does not handle it explicitly.
    """
    if type == mt5.ORDER_TYPE_BUY:
        return mt5.ORDER_TYPE_SELL
    elif type == mt5.ORDER_TYPE_SELL:
        return mt5.ORDER_TYPE_BUY



def getprofit():
    """
    Calculates the total profit from all open positions in MetaTrader 5 (MT5).

    Returns:
    - float: The total profit from all open positions. If no positions are open, the function returns 0.
    
    Behavior:
    - Fetches all current open positions using `mt5.positions_get()`.
    - If no positions are open, prints a message: "No Open Positions" along with the MT5 error code.
    - If there are open positions, iterates through them and sums up the profit (column index 15 in the position data).

    Notes:
    - The code includes commented-out logic for filtering positions by a specific "magic number" (`SCRIPT_MAGIC`).
    - Ensure `mt5` is properly initialized before calling this function.

    Example Usage:
    - Call `getprofit()` after connecting to MT5 to fetch the total profit of all open positions.
    """
    current_profit = 0
    current_profit = mt5.positions_get()
    if current_profit == None:
        print("No Open Positions", ", error code={}".format(mt5.last_error()))
    elif len(current_profit) > 0:  
        profit = 0 
        for profits in current_profit:
            profit += profits[15]
            # Uncomment the following lines to filter by SCRIPT_MAGIC
            # if profits[6] == SCRIPT_MAGIC:
            #     profit += profits[15]
        return profit



def getprofit_single(tick):
    """
    Retrieves the profit for a specific open position in MetaTrader 5 (MT5) based on its ticket number.

    Parameters:
    - tick (int): The ticket number of the position for which to calculate the profit.

    Returns:
    - float: The profit of the specified position. If the position does not exist, the function returns `None`.

    Behavior:
    - Fetches the position associated with the given ticket using `mt5.positions_get(ticket=tick)`.
    - If no position is found, prints a message: "No Open Positions" along with the MT5 error code.
    - If a position is found, iterates through the fetched positions (though typically only one position is returned for a specific ticket).
    - Sums up the profit (column index 15 in the position data) for the specified ticket.

    Notes:
    - Ensure `mt5` is properly initialized and connected before calling this function.
    - The function assumes that the ticket provided is valid and corresponds to an open position.

    Example Usage:
    - Call `getprofit_single(tick)` with a valid ticket number to retrieve the profit of the associated position.
    """
    current_profit = 0
    current_profit = mt5.positions_get(ticket=tick)
    if current_profit == None:
        print("No Open Positions", ", error code={}".format(mt5.last_error()))
    elif len(current_profit) > 0:  
        profit = 0 
        for profits in current_profit:
            profit += profits[15]
            # Uncomment the following lines to filter by SCRIPT_MAGIC
            # if profits[6] == SCRIPT_MAGIC:
            #     profit += profits[15]
        return profit


def open_trade(symbol, lot_size=0.1, stop_loss=100, take_profit=100, deviation=20, b_s = None):
    """
    Opens a trade in MetaTrader 5 (MT5) for the specified symbol with the given parameters.

    Parameters:
    - symbol (str): The trading symbol (e.g., "EURUSD") for which the trade will be opened.
    - lot_size (float, optional): The volume of the trade in lots. Default is 0.1.
    - stop_loss (float, optional): The stop-loss level in points. Default is 100.
    - take_profit (float, optional): The take-profit level in points. Default is 100.
    - deviation (int, optional): Maximum price deviation in points to accept. Default is 20.
    - b_s (bool, optional): Determines the trade type:
        - `True` for a BUY order.
        - `False` for a SELL order.

    Global Variables:
    - pipp: Stores the price at which the trade was executed.
    - is_buy: Indicates whether the trade is a BUY or SELL.

    Returns:
    - int: The ticket number of the opened position if the trade is successful.
    - None: If the trade fails to execute.

    Behavior:
    1. Validates the symbol's availability in the MarketWatch window. 
       - If the symbol is not visible, attempts to add it.
       - If the symbol cannot be added, the function exits.
    2. Prepares a trading request based on the parameters provided:
       - Determines the price and order type (BUY/SELL).
       - Includes additional metadata like order filling type, magic number, and version comment.
    3. Sends the trading request using `mt5.order_send()`.
       - On success: Calculates intermediate price levels and stores them in `opened_positions`.
       - On failure: Logs the detailed error information and shuts down the MT5 terminal.
    4. Prints whether the trade was successfully opened (BUY/SELL) and returns the order ticket.

    Notes:
    - Ensure `mt5` is properly initialized and connected before calling this function.
    - The function includes placeholder logic for stop-loss and take-profit calculations, which are commented out.
    - `SCRIPT_MAGIC` and `SCRIPT_VERSION` must be defined globally for the function to work correctly.
    - The `opened_positions` list should be initialized globally to store position details.

    Example Usage:
    - `open_trade("EURUSD", lot_size=0.2, stop_loss=50, take_profit=100, deviation=10, b_s=True)`
      Opens a BUY position for EURUSD with specified parameters.
    """
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
    """
    Modifies an existing trade in MetaTrader 5 (MT5) by updating the stop-loss (SL) and take-profit (TP) levels.

    Parameters:
    - symbol (str, optional): The trading symbol (e.g., "EURUSD") for the trade to be modified.
    - deviation (int, optional): Maximum price deviation in points to accept. Default is 20.
    - pos_ticket (int, optional): The ticket number of the position to be modified.
    - new_stop (float, optional): The new stop-loss price. Can be set to `None` to skip modification.
    - new_take (float, optional): The new take-profit price. Can be set to `None` to skip modification.

    Global Variables:
    - pipp: Tracks the price of the trade (not directly used here but assumed to be relevant globally).
    - is_buy: Indicates whether the trade was a BUY or SELL (required for determining the price type).

    Returns:
    - None: Logs the success or failure of the modification operation.

    Behavior:
    1. Validates the trading symbol's availability in MarketWatch.
       - If the symbol is not visible, attempts to add it.
       - If the symbol cannot be added, the function exits.
    2. Prepares a modification request using `mt5.TRADE_ACTION_SLTP`.
       - Includes position ticket, new stop-loss, and take-profit levels.
    3. Sends the request using `mt5.order_send()` and evaluates the result.
       - On success: Logs the successful modification.
       - On failure: Prints detailed error information.
    4. The function gracefully shuts down MT5 in case of errors.

    Example Usage:
    - `modify_trade("EURUSD", pos_ticket=12345678, new_stop=1.1050, new_take=1.1250)`
      Modifies the SL and TP of the trade with ticket 12345678 for the EURUSD pair.

    Notes:
    - Ensure `mt5` is properly initialized and connected before calling this function.
    - The `is_buy` variable should be defined globally to determine the price type (ask or bid).
    - `SCRIPT_MAGIC` must be defined globally for the request metadata.
    """
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
    """
    Closes an existing trade in MetaTrader 5 (MT5).

    Parameters:
    - ticket (int): The position ticket number to close.
    - symbol (str): The trading symbol (e.g., "EURUSD") of the trade to close.
    - lot (float): The volume (in lots) to close.
    - typee (int): The original order type (e.g., mt5.ORDER_TYPE_BUY or mt5.ORDER_TYPE_SELL).
    - message (str, optional): Custom message to send as a notification upon closure.

    Global Variables:
    - reverse_type(): A function to reverse the order type for closing the trade.
    - send_notification(): A function to send notifications.

    Returns:
    - None: Logs the success or failure of the close operation.

    Example Usage:
    - `close_trade(ticket=12345678, symbol="EURUSD", lot=1.0, typee=mt5.ORDER_TYPE_BUY, message="Max profit reached.")`

    Notes:
    - Ensure `mt5` is properly initialized and connected before calling this function.
    - `reverse_type(typee)` must return the opposite order type for closing the trade.
    - `send_notification(title, text)` should be implemented for sending notifications.
    """
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
    """
    Closes open positions in MetaTrader 5 that exceed the specified drawdown (maximum position risk).

    Parameters:
    - max_position_risk (float): The maximum allowed drawdown before a position is closed.

    Returns:
    - None: Logs the closing of positions and any errors encountered.
    """
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
    """
    Rounds a number to the nearest 0.2.

    Parameters:
    - number (float): The number to be rounded.

    Returns:
    - float: The number rounded to the nearest 0.2.
    """
    return round(number * 5) / 5

def check_closed_positions():
    """
    Checks for positions that have been closed and sends a notification for each closed position.

    This function iterates over the list of `double_logged_trades` (trades that were logged but not closed)
    and checks if each trade has been closed by querying MetaTrader 5 for the position status. If the position
    is closed, the function retrieves the symbol, trade ID, and closing price, then sends a notification about the closed trade.
    It also removes the closed trade from the `double_logged_trades` list to keep the list updated.

    Parameters:
    None

    Returns:
    None
    """
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
