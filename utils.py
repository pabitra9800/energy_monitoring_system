# utils.py

from collections import defaultdict
from datetime import datetime
from config import TIME_INTERVAL_HOURS

def calculate_energy(readings):
    """Calculate energy usage (kWh) per appliance"""
    usage = defaultdict(float)
    for r in readings:
        usage[r['appliance_id']] += (r['power_watts'] / 1000) * TIME_INTERVAL_HOURS
    return dict(usage)


def latest_by_appliance(readings):
    """Get latest reading per appliance"""
    latest = {}
    for r in reversed(readings):
        if r['appliance_id'] not in latest:
            latest[r['appliance_id']] = r
    return latest


def is_in_time_range(hour, start, end):
    """Check if hour is in start-end range (supports wrapping around midnight)"""
    if start <= end:  # normal range
        return start <= hour <= end
    else:  # wraps around midnight
        return hour >= start or hour <= end


def group_by_hour(readings):
    """Return hourly kWh usage dict"""
    usage_by_hour = defaultdict(float)
    for r in readings:
        ts = datetime.fromisoformat(r["timestamp"])
        usage_by_hour[ts.hour] += (r["power_watts"] / 1000) * TIME_INTERVAL_HOURS
    return dict(usage_by_hour)
