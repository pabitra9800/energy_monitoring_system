from storage import add_reading, get_readings, get_database_stats
from datetime import datetime

def test_mongodb():
    print("Testing MongoDB integration...")
    
    # Test adding a reading
    test_reading = {
        "appliance_id": "appliance_1",
        "power_watts": 45,
        "timestamp": datetime.now().isoformat()
    }
    
    result = add_reading(test_reading)
    if result:
        print(f"✅ Successfully added reading with ID: {result}")
    else:
        print("❌ Failed to add reading")
        return
    
    # Test fetching readings
    readings = get_readings(limit=10)
    print(f"✅ Fetched {len(readings)} readings")
    
    # Test database stats
    stats = get_database_stats()
    print(f"✅ Database stats: {stats}")
    
    print("MongoDB integration test completed!")

if __name__ == "__main__":
    test_mongodb()