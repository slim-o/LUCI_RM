import pandas as pd
import pymongo
from pymongo import MongoClient
import time
import subprocess
from datetime import datetime
import threading
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv() 
# Connect to MongoDB
myclient = MongoClient(os.getenv("MONGO_CLIENT"))
mydb = myclient["Risk_Manager"]
elementsCol = mydb["elements"]
instancesCol = mydb["instances"]

# Function to fetch and display all documents from the "elements" collection
def fetch_elements():
    all_elements = list(elementsCol.find())
    df = pd.DataFrame(all_elements)
    print("Current elements in the database:")
    print(df)
    print('')

# Function to reset the STATUS of instances that have not pinged in over 5 minutes
def reset_expired_instances():
    while True:
        current_time = int(time.time())  # Get the current Unix timestamp
        five_minutes_ago = current_time - 300  # Calculate the timestamp for 5 minutes ago
        
        # Find instances where last_ping is older than 5 minutes
        expired_instances = instancesCol.find({"last_ping": {"$lt": five_minutes_ago}})
        
        for instance in expired_instances:
            instance_id = instance["_id"]
            # Update the instance's STATUS to 'FREE'
            instancesCol.update_one({"_id": instance_id}, {"$set": {"STATUS": "FREE"}})
            print(f"Instance {instance_id} STATUS reset to FREE due to inactivity.")

        time.sleep(60)  # Wait for a minute before checking again

def set_active_elements():
    while True:
        current_time = int(time.time())  # Get the current Unix timestamp
        five_minutes_ago = current_time - 300  # Calculate the timestamp for 5 minutes ago
        
        # Find instances where last_ping is older than 5 minutes
        expired_instances = elementsCol.find({"last_ping": {"$lt": five_minutes_ago}})
        
        for instance in expired_instances:
            element_id = instance["_id"]
            # Update the instance's STATUS to 'FREE'
            elementsCol.update_one({"_id": element_id}, {"$set": {"STATUS": "INACTIVE"}})
            print(f"Instance {element_id} STATUS reset to INACTIVE due to inactivity.")

        time.sleep(60)  # Wait for a minute before checking again

# Function to print the new or updated element
def print_element(element):
    print("Element details:")
    print(pd.DataFrame([element]))
    print('')

# Function to launch Python script in a new terminal if a FREE instance is available
def launch_instance(element_id, account_server):
    # Find an instance with the same server and STATUS 'FREE'
    available_instance = instancesCol.find_one({"server": account_server, "STATUS": "FREE"})
    
    if available_instance:
        instance_path = available_instance['terminal_path']  # Path to the MT5 terminal executable
        instance_id = available_instance['_id']  # Instance ID for STATUS update
        
        # Update the instance's STATUS to 'OCCUPIED'
        instancesCol.update_one({"_id": instance_id}, {"$set": {"STATUS": "OCCUPIED"}})
        
        # Command to run the Python script in a new terminal and pass variables
        script_path = "risk_management.py"  # Path to the Python script you want to launch
        command = (
            f'start cmd.exe /k python "{script_path}" '
            f'--element_id={element_id} --pathway="{instance_path}" --instance="{instance_id}"'
        )
        
        # Print the command to verify it before execution
        print("Command to execute:", command)
        
        # Launch the Python script in a new command prompt window
        subprocess.Popen(command, shell=True)  # Runs the command in a new command prompt window
        
        return f"Instance launched for element {element_id}."
    
    else:
        return f"No available instance for server {account_server}."

# Fetch and display initial data
fetch_elements()

# Start the reset function in a separate thread
reset_thread = threading.Thread(target=reset_expired_instances)
reset_thread.daemon = True  # Daemonize thread to exit when main program does
reset_thread.start()

set_thread = threading.Thread(target=set_active_elements)
set_thread.daemon = True
set_thread.start()

# Monitor changes using MongoDB Change Streams
with elementsCol.watch() as stream:
    print("Watching for changes in the 'elements' collection...")
    for change in stream:
        operation = change['operationType']
        
        if operation == 'insert':
            print("New element inserted:")
            new_element = change['fullDocument']
            print_element(new_element)  # Print the new element details
            
            # Extract the element ID and account server
            element_id = new_element.get('_id')  # MongoDB document ID
            account_server = new_element.get('account_server')
            
            # Launch the instance with the element ID and account server
            result = launch_instance(element_id, account_server)
            print(result)

        elif operation == 'update':
            # Fetch the updated document using its _id
            updated_element_id = change['documentKey']['_id']
            updated_element = elementsCol.find_one({"_id": updated_element_id})
            print("Element updated:")
            print_element(updated_element)  # Print the updated element details
        
        elif operation == 'delete':
            deleted_element_id = change['documentKey']['_id']
            print(f"Element with _id {deleted_element_id} was deleted.")

        # Introduce a short delay before checking for the next change
        time.sleep(1)
