README for Risk Management System
Overview
This system is designed to manage trading accounts on MetaTrader 5 (MT5) using MongoDB to store account data and track the status of instances (MT5 terminals). It includes two primary components:

adm.py: The administrative script responsible for managing instances of MT5 terminals, including resetting the status of inactive instances and launching new instances.
risk_management.py: The script that handles the risk management logic for each account, ensuring that trading accounts stay within predefined risk parameters (e.g., maximum daily loss, maximum risk per position).
The system uses MongoDB to store and manage data about elements (trading accounts) and instances (MT5 terminals), and integrates with MetaTrader 5 to monitor and manage trading activities.

Requirements
Python 3.x
pymongo: To interact with MongoDB
pandas: For displaying and manipulating data
MetaTrader 5: Installed and configured
MongoDB Atlas: A MongoDB database to store account and instance information
MT5 API: For interacting with MetaTrader 5 to fetch account information and manage trades (requires installation of MetaTrader 5 and appropriate configuration)
You can install the required Python libraries using pip:

bash
Copy code
pip install pymongo pandas
How It Works
1. adm.py
This script manages the monitoring of trading instances and elements in the MongoDB database. It:

Fetches elements from the MongoDB collection and prints them in a tabular format using pandas.
Resets expired instances: Periodically checks if any instances have not pinged in the last 5 minutes. If so, it updates their status to "FREE".
Sets elements to inactive: Similarly checks the elements collection for inactivity and updates their status to "INACTIVE".
Launches new instances: When a new element is inserted into the database, it checks for available instances with the status "FREE" and launches a new trading session by running risk_management.py.
To run this script, simply execute it:

bash
Copy code
python adm.py
It will automatically start watching for changes in the MongoDB collection and respond accordingly.

2. risk_management.py
This script is responsible for managing a trading account's risk parameters. It performs the following:

Fetches account data from MongoDB using the element_id provided when launching the script.
Checks account information: Verifies the server, account number, password, and risk settings (max daily loss, max position risk).
Initializes the account on MetaTrader 5 and fetches the account's balance.
Monitors risk parameters: Continuously checks if the account exceeds maximum risk or profit limits, and updates the status of the account in MongoDB if necessary.
To run this script, it must be invoked from adm.py with the appropriate parameters. It is launched automatically when a new element is inserted in MongoDB and when an available instance is found.

Example
bash
Copy code
python risk_management.py --element_id <element_id> --pathway <path_to_mt5> --instance <instance_id>
MongoDB Structure
This system relies on two collections in the MongoDB database:

elements: Stores account information such as the server, account number, password, and risk settings.
instances: Stores information about MetaTrader 5 terminal instances, including their status (e.g., "FREE", "OCCUPIED") and other relevant details like the terminal path.
Functionality
In adm.py:
Monitoring changes: It watches for changes in the elements collection using MongoDB Change Streams. When a new element is added, the system will automatically launch an instance to handle it.
Instance Resetting: Every minute, it checks for instances that haven't pinged in the last 5 minutes and resets their status to "FREE".
In risk_management.py:
Account Info Retrieval: The script retrieves the account information from MongoDB and initializes the MT5 instance.
Risk Management: The script ensures that the account does not exceed the configured risk parameters, including daily loss, max risk per position, and max profit.
Running the System
Start adm.py to begin the monitoring process.
When new elements are added to the MongoDB database, adm.py will automatically launch the corresponding risk_management.py script for each new element.
The risk_management.py script will run continuously to manage the risk for each account and ensure it stays within the defined limits.
Notes
Make sure the MongoDB database is correctly set up with the required collections (elements and instances) before starting the system.
The risk_management.py script is designed to interact with MetaTrader 5 and requires proper setup of MT5 terminals and API access.
The code assumes the MongoDB URI, database, and collection names are as shown, but they can be modified as needed.
Contributing
Feel free to fork this repository, submit issues, and make pull requests. All contributions are welcome.
