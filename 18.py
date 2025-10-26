"""
Title: Live Battery Monitor Using BonicBot WebSocket API
Description: Streams battery data and fetches latest status every 5 seconds.
"""

from updated_bonicbot_controller import create_websocket_controller
from datetime import datetime
import time

# ========== Robot Connection Info ==========
ROBOT_IP = "10.177.152.30"
ROBOT_PORT = 8080

# ========== Create WebSocket Controller ==========
robot = create_websocket_controller(ROBOT_IP, ROBOT_PORT)

# ========== Live Stream Callback ==========
def battery_callback(data):
    # This runs whenever a new battery packet arrives
    timestamp = datetime.now().strftime("%H:%M:%S")
    voltage = data.get("voltage", "N/A")
    current = data.get("current", "N/A")
    soc = data.get("soc", "N/A")
    temp = data.get("temperature", "N/A")
    print(f"[{timestamp}] 📡 Streamed: Voltage={voltage}V | Current={current}A | SOC={soc}% | Temp={temp}°C")

# ========== Main Logic ==========
if robot.connect():
    print(f"✅ Connected to BonicBot at {ROBOT_IP}:{ROBOT_PORT}")

    # Start battery streaming
    print("🔄 Starting battery stream...")
    robot.start_battery_stream(interval_ms=2000, callback=battery_callback)

    # Periodically fetch battery status every 5 seconds
    print("🧪 Fetching live battery status every 5 seconds...")
    try:
        while True:
            battery_data = robot.get_battery_status()
            if battery_data:
                print("\n🔋 Latest Battery Status:")
                print(f"Voltage     : {battery_data.voltage} V")
                print(f"Current     : {battery_data.current} A")
                print(f"Charge (SOC): {battery_data.soc} %")
                print(f"Temperature : {battery_data.temperature} °C")
                if battery_data.has_error:
                    print(f"⚠️ Battery Error: {battery_data.error_message}")
            else:
                print("⏳ Waiting for battery data...")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user.")
        robot.close()
else:
    print("❌ Failed to connect to BonicBot.")
