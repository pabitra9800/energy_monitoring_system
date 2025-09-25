from pymongo import MongoClient
from datetime import datetime

# MongoDB connection settings
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "energy_monitoring"
COLLECTION_NAME = "readings"

def get_mongo_client():
    """Get MongoDB client connection"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        return client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None

def get_database():
    """Get database instance"""
    client = get_mongo_client()
    if client is not None:
        return client[DATABASE_NAME]
    return None

def get_collection():
    """Get readings collection"""
    db = get_database()
    if db is not None:
        return db[COLLECTION_NAME]
    return None