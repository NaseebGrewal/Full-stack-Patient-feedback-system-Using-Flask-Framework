# this code checks mongodb connection was successful or not

from urllib.parse import quote_plus

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

username = quote_plus("ngrewal240")
password = quote_plus("Ng@.1234567890")
uri = f"mongodb+srv://{username}:{password}@cluster1.1bdcxqo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))
# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
