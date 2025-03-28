import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote_plus
import redis


from dotenv import load_dotenv

# Load the .env file
load_dotenv()


# Create a Redis client
def create_redis_client(redis_host="localhost", redis_port=6379, redis_password=None)-> redis.Redis:


    # Connect to Redis
    redis_client = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=0)
    
    # Send a ping to confirm a successful connection with Redis
    try:
        if redis_client.ping():
            print("Successfully connected to Redis!")
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection failed: {e}")
    
    return redis_client


# Create a MongoDB client
def create_mongo_db_client(username, password)-> MongoClient:
 # This contains special characters that need to be encoded


    # URL-encode the username and password
    encoded_username = quote_plus(username)
    encoded_password = quote_plus(password)


    # Create the MongoDB URI using the encoded username and password
    uri = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster1.1bdcxqo.mongodb.net/?appName=Cluster1"


    # Create a new client and connect to the server
    MongoDB_Client = MongoClient(uri, server_api=ServerApi('1'),tls=True)

    # Connect to the database
    # Send a ping to confirm a successful connection
    try:
        MongoDB_Client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
        print("Failed to connect to MongoDB. Check your connection.")

    return MongoDB_Client

