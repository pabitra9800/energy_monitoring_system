from datetime import datetime, timedelta
from db_config import get_collection
from pymongo import DESCENDING

def add_reading(reading):
    """Add a reading to MongoDB"""
    try:
        collection = get_collection()
        if collection is not None:
            # Add MongoDB ObjectId automatically
            result = collection.insert_one(reading)
            print(f"Reading added successfully: {result.inserted_id}")
            return result.inserted_id
        else:
            print("Failed to connect to MongoDB collection")
            return None
    except Exception as e:
        print(f"Error adding reading: {e}")
        return None

def get_readings(limit=20000, hours_back=24):
    """Get readings from MongoDB with optional filtering"""
    try:
        collection = get_collection()
        if collection is not None:
            # Get readings from last 24 hours by default
            since = datetime.now() - timedelta(hours=hours_back)
            
            cursor = collection.find(
                {"timestamp": {"$gte": since.isoformat()}},
                {"_id": 0}  # Exclude MongoDB ObjectId from results
            ).sort("timestamp", DESCENDING).limit(limit)
            
            readings = list(cursor)
            print(f"Fetched {len(readings)} readings from MongoDB")
            return readings
        else:
            print("Failed to connect to MongoDB collection")
            return []
    except Exception as e:
        print(f"Error fetching readings: {e}")
        return []

def get_readings_by_appliance(appliance_id, hours_back=24):
    """Get readings for specific appliance"""
    try:
        collection = get_collection()
        if collection is not None:
            since = datetime.now() - timedelta(hours=hours_back)
            
            cursor = collection.find(
                {
                    "appliance_id": appliance_id,
                    "timestamp": {"$gte": since.isoformat()}
                },
                {"_id": 0}
            ).sort("timestamp", DESCENDING)
            
            return list(cursor)
        else:
            return []
    except Exception as e:
        print(f"Error fetching appliance readings: {e}")
        return []

def clear_old_readings(days_old=30):
    """Remove readings older than specified days"""
    try:
        collection = get_collection()
        if collection is not None:
            cutoff = datetime.now() - timedelta(days=days_old)
            result = collection.delete_many(
                {"timestamp": {"$lt": cutoff.isoformat()}}
            )
            print(f"Deleted {result.deleted_count} old readings")
            return result.deleted_count
        return 0
    except Exception as e:
        print(f"Error clearing old readings: {e}")
        return 0

def get_database_stats():
    """Get database statistics"""
    try:
        collection = get_collection()
        if collection is not None:
            total_readings = collection.count_documents({})
            latest_reading = collection.find_one(
                sort=[("timestamp", DESCENDING)]
            )
            stats = {
                "total_readings": total_readings,
                "latest_timestamp": latest_reading.get("timestamp") if latest_reading else None
            }
            print(f"Database stats: {stats}")
            return stats
        return {"total_readings": 0, "latest_timestamp": None}
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {"total_readings": 0, "latest_timestamp": None}