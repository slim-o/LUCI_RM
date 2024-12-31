import pymongo
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    print("Loading environment variables...")
    load_dotenv()
    mongo_client = os.getenv("MONGO_CLIENT")

    if not mongo_client:
        print("Error: MONGO_CLIENT environment variable is not set.")
        return

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = pymongo.MongoClient(mongo_client)
    db = client["Risk_Manager"]
    elements_col = db["elements"]

    print("Add a new account to the risk manager database:")

    # Collect data for the new element
    try:
        print("Collecting data for the new account...")
        account_number = input("Enter Account Number: ").strip()
        print(f"Account Number entered: {account_number}")
        print('')
        account_pw = input("Enter Account Password: ").strip()
        print("Account Password entered.")
        print('')
        account_server = input("Enter Account Server: ").strip()
        print(f"Account Server entered: {account_server}")
        print('')
        status = "INACTIVE"  # Default status for a new account
        email = input("Enter Email: ").strip()
        print(f"Email entered: {email}")
        print('')
        max_risk_per_position = float(input("Enter Max Risk Per Position: ").strip())
        print(f"Max Risk Per Position entered: {max_risk_per_position}")
        print('')
        max_daily_loss = float(input("Enter Max Daily Loss: ").strip())
        print(f"Max Daily Loss entered: {max_daily_loss}")
        print('')
        max_profit = float(input("Enter Max Profit: ").strip())
        print(f"Max Profit entered: {max_profit}")
        print('')

        # Create the new document
        print("Creating the new account document...")
        new_element = {
            "account_number": account_number,
            "account_pw": account_pw,
            "account_server": account_server,
            "STATUS": status,
            "email": email,
            "max_risk_per_position": max_risk_per_position,
            "max_daily_loss": max_daily_loss,
            "max_profit": max_profit
        }

        # Insert the new document into the collection
        print("Inserting the new account into the database...")
        result = elements_col.insert_one(new_element)
        print(f"New account added successfully with ID: {result.inserted_id}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
