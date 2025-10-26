from updated_bonicbot_controller import create_websocket_controller
import time

# === CONFIG ===
ROBOT_IP = "10.177.152.30"
WEBSOCKET_PORT = 8080
MJPEG_PORT = 8081
MJPEG_STREAM = f"http://{ROBOT_IP}:{MJPEG_PORT}/stream"

# Create controller
controller = create_websocket_controller(ROBOT_IP, WEBSOCKET_PORT)

if controller.connect():
    print("✅ WebSocket connected to BonicBot")
    print(f"🎥 MJPEG Stream available at: {MJPEG_STREAM}")

    # Keep connection alive for 5 seconds
    print("⏳ Keeping WebSocket open for 5 seconds...")
    time.sleep(5)

    # Disconnect
    controller.close()
    print("🔌 WebSocket disconnected.")
else:
    print("❌ Failed to connect to BonicBot")

