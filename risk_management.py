import argparse
import pymongo
from bson.objectid import ObjectId
from variables_general import *
import time
from datetime import datetime

ticket = 0
lot_sizerr = 9
entry_price = 10
stop_loss = 11
take_profit = 12
current_profit = 17
current_symbol = 16

max_position_risk = 0  # Initialize with a proper value like 0
MAX_L = 0  # Initialize max daily loss
MAX_P = 0  # Initialize max profit
initial_balance = 0  # Initialize initial balance

instance_path = None
account_number = None
account_password = None
account_server = None
instance_id = None
reset_values = True

#element_id = '670668499589fb938aa11f88'
#instance_path = 'C:/Program Files/MetaTrader 5 IC Markets (SC)/terminal64.exe'
#instance_id = '670d34492d1e85ac874b005e'

def main():
    global max_position_risk, MAX_L, MAX_P, initial_balance, account_number, account_password, account_server, instance_path, instance_id, instancesCol, element_id, elementsCol
    
    # Set up the argument parser
    parser = argparse.ArgumentParser(description='Process account information for MT5 instance.')
    
    parser.add_argument('--element_id', required=True, help='The MongoDB element ID to fetch account info')
    parser.add_argument('--pathway', required=True, help='The path to the MT5 terminal executable')
    parser.add_argument('--instance', required=True, help='element id for instance')
    
    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Access the arguments
    element_id = args.element_id
    instance_path = args.pathway
    instance_id = args.instance  # Assign it to the global variable
    #element_id = '6712399de6e8540f25e71759'
    #instance_path = 'C:/Program Files/FTMO MetaTrader 5/terminal64.exe'
    #instance_id = '670d34492d1e85ac874b005e'

    ###########################
    # Connect to MongoDB to fetch account info
    myclient = pymongo.MongoClient('mongodb+srv://jonway:PxPwYzONXRcO1hxA@luci-1.nwqlw4u.mongodb.net/Risk_Manager')
    mydb = myclient["Risk_Manager"]
    elementsCol = mydb["elements"]
    instancesCol = mydb["instances"]  # This is the collection used in the while loop
    
    try:
        # Convert element_id to ObjectId for querying
        element_id_obj = ObjectId(element_id)
        
        # Fetch the account details using the ObjectId
        account_info = elementsCol.find_one({"_id": element_id_obj})
        
        if account_info:
            # Extract account details and print them for debugging
            account_server = account_info.get('account_server')
            account_number = account_info.get('account_number')
            account_password = account_info.get('account_pw')
            max_prof = account_info.get('max_profit')
            max_loss = account_info.get('max_daily_loss')
            max_position = account_info.get('max_risk_per_position')
            
            # Debugging output
            print(f"Account Info Retrieved: {account_info}")
            print(f"Server: {account_server}, Account: {account_number}, Password: {account_password}")
            
            # Check if credentials are valid
            if not account_server or not account_number or not account_password:
                raise ValueError("Account credentials missing or incomplete. Check MongoDB data.")

            # Set the max values
            max_position_risk += max_position or 0  # Ensure None is handled
            MAX_L += max_loss or 0  # Handle None
            MAX_P += max_prof or 0  # Handle None

            # Initialize the instance and account info
            retryable_initialize(3, 5, instance_path, account_number, account_password, account_server)
            initial_account = mt5.account_info()
            initial_balance = initial_account[10]
            print(f'Initial Balance: {initial_balance}')
            print(f'Max Equity +: {MAX_P + initial_balance}')
            print(f'Max Equity -: {initial_balance - MAX_L}')
            print(f'Max Risk Per Position: {max_position_risk}')

            elementsCol.update_one(
                {'_id': element_id_obj},  # Match the document by instance ID
                {'$set': {'STATUS': "ACTIVE"}}  # Update the last_ping with current Unix time
            )
            print('STATUS set to ACTIVE')
        else:
            print(f"No account found with element_id {element_id}")
            raise ValueError(f"No account found in MongoDB with element_id {element_id}")
    except Exception as e:
        print(f"Error fetching account: {e}")

if __name__ == "__main__":
    main()
    
    # Start the while loop to manage the account
    while True:

        try:
            element_id_obj = ObjectId(element_id)

            account_info = elementsCol.find_one({"_id": element_id_obj})
            if account_info:
                max_prof = account_info.get('max_profit')
                max_loss = account_info.get('max_daily_loss')
                max_position = account_info.get('max_risk_per_position')

                max_position_risk = 0
                MAX_L = 0
                MAX_P = 0

                max_position_risk += max_position or 0  # Ensure None is handled
                MAX_L += max_loss or 0  # Handle None
                MAX_P += max_prof or 0  # Handle None
                print(max_position_risk)
                print(MAX_L)
                print(MAX_P)
                print('VALUES UP TO DATE')
                print('ACTIVE')
            else:
                print('element deleted, stop script')
                quit()
            current_time = datetime.now().time()
            
            start_time = current_time.replace(hour=23, minute=0, second=0, microsecond=0)
            end_time = current_time.replace(hour=23, minute=1, second=0, microsecond=0)
            rest_time = current_time.replace(hour=23, minute=2, second=0, microsecond=0)
            
            if current_time >= rest_time:
                reset_values = True

            if reset_values:
                if start_time <= current_time <= end_time:
                    print("RESET: The time is between 23:00 and 23:10.")
                    initial_balance = 0
                    initial_account = mt5.account_info()
                    initial_balance = initial_account[10]
                    reset_values = False
                

            ###### PING
            instance_id_obj = ObjectId(instance_id)
            current_unix_time = int(time.time())
            instancesCol.update_one(
                {'_id': instance_id_obj},  # Match the document by instance ID
                {'$set': {'last_ping': current_unix_time}}  # Update the last_ping with current Unix time
            )

            
            elementsCol.update_one(
                {'_id': element_id_obj},  # Match the document by instance ID
                {'$set': {'last_ping': current_unix_time}}  # Update the last_ping with current Unix time
            )



            ###### PING

            # Retry initialization and get account equity
            if account_number and account_password and account_server:
                retryable_initialize(3, 5, instance_path, account_number, account_password, account_server)
            else:
                raise ValueError("Account credentials missing.")

            account_equity = (mt5.account_info())[13]

            open_profit = 0
            positions_total = mt5.positions_total()

            if positions_total > 0:
                open_profit += getprofit()

            close_positions_in_drawdown(max_position_risk)

            # Check if account equity exceeds max profit or loss limits
            if account_equity >= (MAX_P + initial_balance):
                print('Max profit hit: Closing all trades')
                live_positions = mt5.positions_get()

                if live_positions is None:
                    print(f"No open positions, error code: {mt5.last_error()}")
                elif len(live_positions) > 0:
                    for posit in live_positions:
                        priche = mt5.symbol_info_tick(posit[16]) 
                        print(priche)
                        close_trade(posit[0], posit[16], posit[9], posit[5], message='Trades Closed')
                
                send_notification(f'{SCRIPT_VERSION} SHUTDOWN', 'MAX PROFIT HIT')
                #quit() # dont quit, what if more trades are taken 

            elif account_equity <= (initial_balance - MAX_L):
                print('Max loss hit: Closing all trades')
                live_positions = mt5.positions_get()

                if live_positions is None:
                    print(f"No open positions, error code: {mt5.last_error()}")
                elif len(live_positions) > 0:
                    for posit in live_positions:
                        priche = mt5.symbol_info_tick(posit[16]) 
                        print(priche)
                        close_trade(posit[0], posit[16], posit[9], posit[5], message='Trades Closed')

                send_notification(f'{SCRIPT_VERSION} SHUTDOWN', 'MAX LOSS HIT')
                #quit() # dont quit, what if more trades are taken 

            # Sleep briefly before the next loop iteration
            time.sleep(0.5)  # Adjust as needed
            
        except Exception as error:
            print(f"Error in trading loop: {error}")
            send_notification(f'{SCRIPT_VERSION}: ERROR', str(error))
