# app.py

from flask import Flask, jsonify, render_template, request
from collections import defaultdict
from datetime import datetime
import json

from config import APPLIANCE_NAMES, COST_PER_KWH
from storage import add_reading, get_readings
from utils import (
    calculate_energy,
    latest_by_appliance,
    is_in_time_range,
    group_by_hour
)

app = Flask(__name__)

# Load waste rules
with open("config.json", "r") as f:
    CONFIG = json.load(f)

WASTE_RULES = CONFIG["waste_rules"]
SUMMARY_RULES = CONFIG["summary_rules"]
SAVING_TIPS = CONFIG["saving_tips"]

# with open("waste_rules.json") as f:
#     waste_rules = json.load(f)

# with open("saving_tips.json", "r") as f:
#     SAVING_TIPS = json.load(f)

# with open("summary_rules.json", "r") as f:
#     SUMMARY_RULES = json.load(f)


@app.route("/")
def index():
    return render_template("index.html")

APPLIANCE_STATES = {aid: True for aid in APPLIANCE_NAMES}  # All ON by default

@app.route('/appliance_states', methods=['GET'])
def get_appliance_states():
    return jsonify(APPLIANCE_STATES)

@app.route('/appliance_states', methods=['POST'])
def set_appliance_state():
    data = request.get_json()
    aid = data.get('appliance_id')
    state = data.get('state')
    if aid in APPLIANCE_STATES and isinstance(state, bool):
        APPLIANCE_STATES[aid] = state
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/stream', methods=['POST'])
def receive_data():
    data = request.get_json()
    if data and 'power_watts' in data and 'appliance_id' in data:
        data['timestamp'] = datetime.now().isoformat()
        add_reading(data)   # ✅ use storage helper
        return jsonify({"status": "success"}), 200
    
@app.route('/data')
def get_data():
    return jsonify({"readings": get_readings()})  # ✅

@app.route('/daily_counters')
def daily_counters():
    readings = get_readings()
    # Calculate total daily energy and pie chart data
    totals = {}
    for r in readings:
        aid = r['appliance_id']
        if aid not in totals:
            totals[aid] = 0
        totals[aid] += r['power_watts']
    # Convert to kWh
    pie_chart_data = {aid: round((w * 5 / 3600 / 1000), 3) for aid, w in totals.items()}
    total_daily_energy_kwh = sum(pie_chart_data.values())
    return jsonify({
        "total_daily_energy_kwh": total_daily_energy_kwh,
        "pie_chart_data": {aid: v for aid, v in pie_chart_data.items()}
    })

@app.route("/current_usage")
def current_usage():
    readings = get_readings()
    latest = latest_by_appliance(readings)
    data = {
        APPLIANCE_NAMES[appliance]: r["power_watts"]
        for appliance, r in latest.items()
    }
    return jsonify(data)

@app.route("/top_consumer")
def top_consumer():
    readings = get_readings()
    latest = latest_by_appliance(readings)
    if not latest:
        return jsonify({"top_consumer": None})
    top = max(latest.values(), key=lambda x: x["power_watts"])
    return jsonify({
        "top_consumer": APPLIANCE_NAMES[top["appliance_id"]],
        "power": top["power_watts"]
    })

@app.route("/peak_usage")
def peak_usage():
    readings = get_readings()
    usage_by_hour = group_by_hour(readings)
    peak_hour = max(usage_by_hour, key=usage_by_hour.get) if usage_by_hour else None
    return jsonify({
        "usage_by_hour": usage_by_hour,
        "peak_hour": peak_hour
    })

@app.route('/advanced_summary')
def get_advanced_summary():
    """
    Calculates and returns a summary of energy cost and alerts.
    """
    appliance_data = defaultdict(lambda: {"total_energy_kwh": 0, "on_time_minutes": 0})
    time_interval_hours = 5 / 3600
    time_interval_minutes = 5 / 60

    readings = get_readings()
    for reading in readings:
        appliance_id = reading['appliance_id']
        power_watts = reading['power_watts']
        energy_kwh = (power_watts / 1000) * time_interval_hours
        appliance_data[appliance_id]['total_energy_kwh'] += energy_kwh

        if power_watts > 20:  # ON threshold
            appliance_data[appliance_id]['on_time_minutes'] += time_interval_minutes

    most_expensive_appliance = "N/A"
    max_cost = 0
    appliance_costs = {}

    for appliance_id, data in appliance_data.items():
        cost = data['total_energy_kwh'] * COST_PER_KWH
        appliance_costs[appliance_id] = cost
        if cost > max_cost:
            max_cost = cost
            most_expensive_appliance = appliance_id

    # Apply JSON rules
    alerts = []
    # for rule in SUMMARY_RULES["summary_rules"]:
    for rule in SUMMARY_RULES:
        appliance_id = rule["appliance_id"]
        minutes_on = appliance_data[appliance_id]["on_time_minutes"]
        if rule["type"] == "max_on_time":
            if minutes_on > rule["minutes_threshold"]:
                alerts.append(rule["message"])

    return jsonify({
        "most_expensive_appliance": most_expensive_appliance,
        "appliance_costs": appliance_costs,
        "alerts": alerts
    })

@app.route('/waste_alerts')
def get_waste_alerts():
    alerts = []
    time_interval_minutes = 5 / 60  # readings every 5 seconds

    # Track continuous usage (minutes)
    appliance_on_time = defaultdict(float)
    readings = get_readings()
    for r in readings:
        if r['power_watts'] > 20:  # generic ON threshold
            appliance_on_time[r['appliance_id']] += time_interval_minutes

    # Apply rules
    # for rule in WASTE_RULES["rules"]:
    for rule in WASTE_RULES:
        appliance_id = rule["appliance_id"]
        readings = get_readings()

        # 1. Night time usage
        if rule["type"] == "time_range":
            for r in readings[-50:]:  # check last ~4 minutes
                if (r['appliance_id'] == appliance_id and r['power_watts'] > rule.get("power_threshold", 0)):
                    ts = datetime.fromisoformat(r['timestamp'])
                    if ts.hour >= rule["start_hour"] or ts.hour <= rule["end_hour"]:
                        alerts.append(rule["message"])

        # 2. Continuous usage
        if rule["type"] == "continuous_usage":
            minutes_on = appliance_on_time.get(appliance_id, 0)
            if minutes_on > rule["minutes_threshold"]:
                alerts.append(rule["message"])

        # 3. Abnormal usage
        if rule["type"] == "abnormal_usage":
            for r in readings[-rule["duration_readings"]:]:
                if (r['appliance_id'] == appliance_id and r['power_watts'] > rule.get("power_threshold", 0)):
                    alerts.append(rule["message"])
                    break

    return jsonify({"alerts": alerts})

@app.route('/saving_tips')
def get_saving_tips():
    time_interval_hours = 5 / 3600
    costs = defaultdict(float)
    readings = get_readings()

    # Calculate daily cost per appliance
    for r in readings:
        energy_kwh = (r['power_watts'] / 1000) * time_interval_hours
        costs[r['appliance_id']] += energy_kwh * COST_PER_KWH

    tips = []
    # for rule in SAVING_TIPS["saving_tips"]:
    for rule in SAVING_TIPS:
        appliance_id = rule["appliance_id"]
        if costs.get(appliance_id, 0) > rule["cost_threshold"]:
            tips.append(rule["message"])

    return jsonify({"tips": tips})

@app.route("/dashboard_summary")
def dashboard_summary():
    """Aggregate multiple summaries into one call"""
    readings = get_readings()

    # Current usage
    latest = latest_by_appliance(readings)
    current = {APPLIANCE_NAMES[a]: r["power_watts"] for a, r in latest.items()}

    # Advanced summary
    energy_usage = calculate_energy(readings)
    total = sum(energy_usage.values())
    advanced = {
        "usage_kwh": {APPLIANCE_NAMES[a]: round(v, 3) for a, v in energy_usage.items()},
        "total_kwh": round(total, 3),
        "total_cost": round(total * COST_PER_KWH, 2)
    }

    # Waste alerts
    alerts = []
    time_interval_minutes = 5 / 60  # readings every 5 seconds
    appliance_on_time = defaultdict(float)
    for r in readings:
        if r['power_watts'] > 20:  # generic ON threshold
            appliance_on_time[r['appliance_id']] += time_interval_minutes

    for rule in WASTE_RULES:
        appliance_id = rule["appliance_id"]

        # 1. Night time usage
        if rule["type"] == "time_range":
            for r in readings[-50:]:  # check last ~4 minutes
                if (r['appliance_id'] == appliance_id and r['power_watts'] > rule.get("power_threshold", 0)):
                    ts = datetime.fromisoformat(r['timestamp'])
                    if is_in_time_range(ts.hour, rule["start_hour"], rule["end_hour"]):
                        alerts.append(rule["message"])
                        break

        # 2. Continuous usage
        if rule["type"] == "continuous_usage":
            minutes_on = appliance_on_time.get(appliance_id, 0)
            if minutes_on > rule["minutes_threshold"]:
                alerts.append(rule["message"])

        # 3. Abnormal usage
        if rule["type"] == "abnormal_usage":
            for r in readings[-rule["duration_readings"]:]:
                if (r['appliance_id'] == appliance_id and r['power_watts'] > rule.get("power_threshold", 0)):
                    alerts.append(rule["message"])
                    break

    return jsonify({
        "current_usage": current,
        "advanced_summary": advanced,
        "alerts": alerts
    })


if __name__ == "__main__":
    app.run(debug=True)
