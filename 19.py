import time
import json
from updated_bonicbot_controller import create_websocket_controller

# === Connect to BonicBot ===
controller = create_websocket_controller(host="10.177.152.30", port=8080)

if not controller.connect():
    print("❌ Could not connect to BonicBot.")
    exit()

print("✅ Connected to BonicBot WebSocket\n")

# === Request BMS Reading ===
controller.read_battery()

# === Wait for Latest BMS Data ===
def wait_for_bms_data(timeout=10):
    print("⏳ Waiting for battery (BMS) data...")
    for _ in range(timeout * 2):  # check every 0.5 sec
        data = controller.get_latest_sensor_data("battery")
        if data and "data" in data:
            return data["data"]
        time.sleep(0.5)
    return None

# === Fetch and Print JSON ===
bms_data = wait_for_bms_data()

if bms_data:
    print("🔋 Latest BMS Data (JSON):")
    print(json.dumps(bms_data, indent=2))
else:
    print("⚠️ No BMS data received.")

# === Disconnect ===
controller.close()
print("\n🔌 Disconnected from BonicBot")
