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


# def latest_by_appliance(readings):
    """Get latest reading per appliance"""
    latest = {}
    for r in reversed(readings):
        if r['appliance_id'] not in latest:
            latest[r['appliance_id']] = r
    return latest

def latest_by_appliance(readings):
    """
    Return a dict of latest reading per appliance_id.
    Keys: appliance_id, Values: full reading dict (most recent by timestamp).
    """
    latest = {}
    # helper to parse timestamp (handle datetime or ISO string)
    def _ts(r):
        ts = r.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.min

    # sort readings newest first and pick first occurrence per appliance
    for r in sorted(readings, key=_ts, reverse=True):
        aid = r.get("appliance_id")
        if aid and aid not in latest:
            latest[aid] = r
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
