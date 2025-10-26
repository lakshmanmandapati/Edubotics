#!/usr/bin/env python3
"""
Demo: Reading Motor, Servo, and Eye Display Data via WebSocket
"""

import time
from updated_bonicbot_controller import create_websocket_controller

def main():
    # Create a WebSocket controller (adjust host/port if needed)
    robot = create_websocket_controller(host="10.177.152.30", port=8080)

    print("🔌 Connecting to BonicBot via WebSocket...")
    if not robot.connect():
        print("❌ Failed to connect to BonicBot WebSocket server")
        return
    print("✅ Connected!")

    # --- Start streaming sensor data ---
    print("📡 Starting sensor streams (motors, servos, head)...")
    robot.start_base_stream(interval_ms=500)       # Motors
    robot.start_right_hand_stream(interval_ms=500) # Right hand servos
    robot.start_left_hand_stream(interval_ms=500)  # Left hand servos
    robot.start_head_stream(interval_ms=500)       # Head servos (eyes)

    try:
        for _ in range(20):  # Collect 20 updates
            time.sleep(1.0)

            # Get motor readings
            motors = robot.get_base_motor_readings()
            if motors:
                print("\n⚙️ Motor Readings:")
                for name, m in motors.items():
                    print(f" {name}: speed={m.feedback_speed}, "
                          f"pos={m.feedback_position}, torque={m.torque}, "
                          f"temp={m.temperature}")

            # Get servo readings (right hand example)
            right_servos = robot.get_hand_servo_readings(is_right=True)
            if right_servos:
                print("\n🤖 Right Hand Servo Readings:")
                for name, s in right_servos.items():
                    print(f" {name}: angle={s.feedback_angle}, "
                          f"speed={s.feedback_speed}, load={s.load}, "
                          f"temp={s.temperature}, error={s.has_error}")

            # Get head/eye servo readings
            head_servos = robot.get_head_servo_readings()
            if head_servos:
                print("\n👀 Head (Eye) Servo Readings:")
                for name, s in head_servos.items():
                    print(f" {name}: angle={s.feedback_angle}, "
                          f"speed={s.feedback_speed}, load={s.load}, "
                          f"temp={s.temperature}, error={s.has_error}")

    except KeyboardInterrupt:
        print("🛑 Stopping monitoring...")

    finally:
        robot.close()
        print("🔒 Disconnected")

if __name__ == "__main__":
    main()
