import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Define your username and password
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD_MONGODB')   # This contains special characters that need to be encoded

# URL-encode the username and password
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

# Create the MongoDB URI using the encoded username and password
uri = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster1.1bdcxqo.mongodb.net/?appName=Cluster1"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'),tls=True)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)