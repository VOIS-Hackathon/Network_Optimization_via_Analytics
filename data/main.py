import json
import random
from datetime import datetime, timedelta

uk_locations = [
    (51.5074, -0.1278),   # London
    (53.4808, -2.2426),   # Manchester
    (55.9533, -3.1883),   # Edinburgh
    (52.4862, -1.8904),   # Birmingham
    (51.4545, -2.5879),   # Bristol
    (57.1497, -2.0943),   # Aberdeen
    (50.8225, -0.1372),   # Brighton
    (54.9783, -1.6178),   # Newcastle
    (51.7520, -1.2577),   # Oxford
    (53.4084, -2.9916)    # Liverpool
]

def generate_data(num_rows):
    data = []
    base_time = datetime(2025, 8, 22, 0, 0)
    for i in range(num_rows):
        lat, lon = random.choice(uk_locations)
        bandwidth_value = round(random.uniform(5, 100), 2)
        bandwidth_unit = random.choice(["Mbps", "Gbps"])
        users_connected = random.randint(10, 500)

        # Simulate congestion
        download_speed = round(200 / (1 + users_connected / 50), 2)
        upload_speed = round(80 / (1 + users_connected / 50), 2)

        # Call drop reason with some nulls
        call_drop_reason = random.choices(
            ["Satisfactory", "Poor Voice Quality", "Other", None],
            weights=[0.4, 0.3, 0.25, 0.05]
        )[0]

        record = {
            # 📊 Core Relevant Columns
            "timestamp": (base_time + timedelta(minutes=5*i)).isoformat(),
            "tower_id": f"TWR{random.randint(1000, 1100)}",
            "location": {
                "latitude": round(lat + random.uniform(-0.01, 0.01), 6),
                "longitude": round(lon + random.uniform(-0.01, 0.01), 6)
            },
            "latency_sec": round(random.uniform(0.100, 0.999), 3),
            "bandwidth": f"{bandwidth_value} {bandwidth_unit}",
            "dropped_calls": random.randint(0, 10),
            "total_calls": random.randint(50, 200),
            "uptime_percent": round(random.uniform(95.0, 100.0), 2),
            "network_type": random.choice(["4G", "5G", "LTE"]),
            "operator": random.choice(["Vodafone UK", "EE", "O2", "Three"]),
            "users_connected": users_connected,
            "download_speed_mbps": download_speed,

            # 🧠 10 More Relevant Columns
            "signal_strength_dbm": round(random.uniform(-110, -60), 2),
            "tower_load_percent": round(random.uniform(10.0, 100.0), 2),
            "average_call_duration_sec": round(random.uniform(30, 300), 1),
            "handover_success_rate": round(random.uniform(85.0, 100.0), 2),
            "packet_loss_percent": round(random.uniform(0.0, 5.0), 2),
            "jitter_ms": round(random.uniform(1.0, 20.0), 2),
            "tower_temperature_c": round(random.uniform(10.0, 45.0), 1),
            "battery_backup_hours": round(random.uniform(0.0, 12.0), 1),
            "tower_age_years": random.randint(1, 20),
            "maintenance_due": random.choice([True, False]),
            "download_speed_mbps": download_speed,
            "upload_speed_mbps": upload_speed,
            "call_drop_reason": call_drop_reason,

            # 📶 Signal Strength Metrics
            "signal_strength": {
                "RSSI": round(random.uniform(-120, -60), 2),
                "RSRP": round(random.uniform(-140, -80), 2),
                "SINR": round(random.uniform(-10, 30), 2)
            },

            # 📡 VoIP/Data Quality Metrics
            "voip_metrics": {
                "jitter_ms": round(random.uniform(1.0, 50.0), 2),
                "packet_loss_percent": round(random.uniform(0.0, 5.0), 2)
            },
             "operator": random.choice(["Vodafone UK", "EE", "O2", "Three"]),

            # 🧹 Irrelevant Columns
            "weather_condition": random.choice(["Sunny", "Rainy", "Cloudy", "Foggy"]),
            "technician_notes": random.choice(["", "Checked cables", "Rebooted system", "No issues"]),
            "last_maintenance": (base_time - timedelta(days=random.randint(1, 365))).date().isoformat(),
            "tower_color": random.choice(["Grey", "White", "Red", "Blue"]),
            "is_test_tower": random.choice([True, False]),
            "tower_height_m": round(random.uniform(30.0, 100.0), 2),
            "signal_icon": random.choice(["📶", "🔇", "⚠️", "✅"]),
            "internal_code": f"INT{random.randint(10000, 99999)}",
            "notes": random.choice(["", "Pending upgrade", "Legacy hardware", "Temporary site"]),
            "extra_flag": random.choice(["A", "B", "C", "Z"])
        }
        data.append(record)
    return data

# Generate and save to file
data = generate_data(9000)
with open("telecom_tower_usaged.json", "w") as f:
    json.dump(data, f, indent=2)