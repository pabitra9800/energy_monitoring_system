import json

def process_data(filename="simulated_data.json"):
    """
    Reads simulated data, processes it, and calculates energy usage.
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return None
    
    # Store processed data, categorized by appliance
    processed_data = {}
    
    # Define time interval in hours (since original interval was 60 seconds)
    time_interval_hours = 60 / 3600  # 60 seconds / 3600 seconds per hour
    
    # Process each reading
    for reading in data["sensor_readings"]:
        appliance_id = reading["appliance_id"]
        power_watts = reading["power_watts"]
        
        # Calculate energy for this reading (Energy = Power x Time)
        energy_kwh = (power_watts / 1000) * time_interval_hours  # Convert W to kW
        
        # Initialize appliance data if it's the first reading
        if appliance_id not in processed_data:
            processed_data[appliance_id] = {
                "total_power_watts": 0,
                "total_energy_kwh": 0,
                "readings": []
            }
        
        # Add to total energy and power
        processed_data[appliance_id]["total_power_watts"] += power_watts
        processed_data[appliance_id]["total_energy_kwh"] += energy_kwh
        processed_data[appliance_id]["readings"].append({
            "timestamp": reading["timestamp"],
            "power_watts": power_watts
        })
        
    return processed_data

def display_summary(processed_data):
    """
    Prints a summary of the processed data to the console.
    """
    if not processed_data:
        return
        
    print("--- Energy Consumption Summary ---")
    total_energy_kwh_all = 0
    
    # A simple mapping for appliance IDs
    appliance_names = {
        "appliance_1": "Ceiling Fan 1",
        "appliance_2": "Ceiling Fan 2",
        "appliance_3": "Ceiling Fan 3",
        "appliance_4": "Television",
        "appliance_5": "Refrigerator"
    }

    for appliance_id, data in processed_data.items():
        name = appliance_names.get(appliance_id, f"Appliance {appliance_id}")
        total_energy = data["total_energy_kwh"]
        print(f"{name}: {total_energy:.3f} kWh")
        total_energy_kwh_all += total_energy
        
    print(f"\nTotal Household Energy Consumption: {total_energy_kwh_all:.3f} kWh")
    
    # You can add a simple cost calculation here
    # Assuming an average electricity rate of ₹7 per kWh in India
    cost_per_kwh = 7
    total_cost = total_energy_kwh_all * cost_per_kwh
    print(f"Estimated Cost: ₹{total_cost:.2f}")

if __name__ == "__main__":
    processed_data = process_data()
    if processed_data:
        display_summary(processed_data)