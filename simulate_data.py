import json
import random
import time
import requests
from datetime import datetime, timedelta

APPLIANCES = {
    "appliance_1": {"name": "Ceiling Fan 1", "power_levels": [30, 45, 60]},
    "appliance_2": {"name": "Ceiling Fan 2", "power_levels": [30, 45, 60]},
    "appliance_3": {"name": "Ceiling Fan 3", "power_levels": [30, 45, 60]},
    "appliance_4": {"name": "Television", "power_levels": {"on": 100, "standby": 2}},
    "appliance_5": {"name": "Refrigerator", "power_levels": {"on": 150, "off": 5}}
}

FLASK_SERVER_URL = "http://127.0.0.1:5000/stream"
READING_INTERVAL_SECONDS = 5

# Track refrigerator cycle
fridge_last_toggle = datetime.now()
fridge_state = "on"

def fetch_appliance_states():
    try:
        resp = requests.get("http://127.0.0.1:5000/appliance_states")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Default: all ON if cannot fetch
    return {aid: True for aid in APPLIANCES}

def generate_power_data(appliance_id, current_time):
    profile = APPLIANCES[appliance_id]
    
    if "Fan" in profile["name"]:
        # Fans mostly on daytime
        if 8 <= current_time.hour <= 22:
            return random.choice(profile["power_levels"])
        else:
            return 0  # off at night

    elif "Television" in profile["name"]:
        # TV mostly evening/night
        return profile["power_levels"]["on"]
        # if 18 <= current_time.hour <= 23:
        #     return profile["power_levels"]["on"]
        # else:
        #     return profile["power_levels"]["standby"]

    elif "Refrigerator" in profile["name"]:
        global fridge_last_toggle, fridge_state
        # Toggle every 30-40 minutes
        if (current_time - fridge_last_toggle).total_seconds() > random.randint(1800, 2400):
            fridge_state = "on" if fridge_state == "off" else "off"
            fridge_last_toggle = current_time
        return profile["power_levels"][fridge_state]

    return 0

def simulate_and_send_data():
    print(f"Starting realistic simulation, sending data every {READING_INTERVAL_SECONDS}s...")
    try:
        while True:
            now = datetime.now()
            appliance_states = fetch_appliance_states()
            for appliance_id in APPLIANCES.keys():
                if not appliance_states.get(appliance_id, True):
                    power = 0  # Appliance is OFF
                else:
                    power = generate_power_data(appliance_id, now)
                reading = {
                    "appliance_id": appliance_id,
                    "power_watts": power
                }
                try:
                    response = requests.post(FLASK_SERVER_URL, json=reading)
                    status = "OK" if response.status_code == 200 else f"Failed {response.status_code}"
                    appliance_name = APPLIANCES[appliance_id]["name"]
                    print(f"{now.strftime('%H:%M:%S')} - Sent {appliance_name}: {power}W -> {status}")
                except requests.exceptions.ConnectionError:
                    print("Cannot connect to Flask server. Is it running?")
            time.sleep(READING_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Simulation stopped by user.")

if __name__ == "__main__":
    simulate_and_send_data()
