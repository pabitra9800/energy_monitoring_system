# storage.py

from collections import deque

# Keep last 2000 readings in memory
real_time_readings = deque(maxlen=2000)

def add_reading(reading):
    """Add a reading to storage"""
    real_time_readings.append(reading)

def get_readings():
    """Return all readings as list"""
    return list(real_time_readings)
