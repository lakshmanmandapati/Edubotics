# a1_color_follower.py
import cv2
import numpy as np
import time
from updated_bonicbot_controller import create_websocket_controller

# ====== CONFIG ======
ROBOT_IP = "10.177.152.30"
WS_PORT = 8080
MJPEG_PORT = 8081
STREAM_URL = f"http://{ROBOT_IP}:{MJPEG_PORT}/stream"

ROTATE_ANGLE = 0         # 0, 90, 180, 270
FLIP_HORIZONTAL = True

# HSV ranges for RED (two ranges due to hue wrap-around)
LOWER_RED1 = np.array([0, 120, 70])
UPPER_RED1 = np.array([10, 255, 255])
LOWER_RED2 = np.array([170, 120, 70])
UPPER_RED2 = np.array([180, 255, 255])

# Control thresholds
CENTER_TOLERANCE = 0.15   # how close to center (normalized) before going straight
MIN_AREA = 600            # ignore small noise
CLOSE_AREA = 15000        # stop when target is “very close”
SPEED_BASE = 35
TURN_SPEED = 30
COOLDOWN = 0.25           # seconds between movement commands
# =====================

def rotate_frame(frame, angle):
    if angle == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if angle == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if angle == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame

def main():
    bot = create_websocket_controller(ROBOT_IP, WS_PORT)
    if not bot.connect():
        print("❌ Could not connect to BonicBot")
        return
    print("✅ Connected to BonicBot")

    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("❌ Could not open camera stream")
        bot.close()
        return

    last_cmd = 0.0
    current_action = "stop"

    def send(action):
        nonlocal last_cmd, current_action
        now = time.time()
        if now - last_cmd < COOLDOWN and action == current_action:
            return
        last_cmd = now
        current_action = action
        try:
            if action == "forward":
                bot.move_forward(SPEED_BASE, 0.6)
            elif action == "left":
                bot.turn_left(TURN_SPEED, 0.4)
            elif action == "right":
                bot.turn_right(TURN_SPEED, 0.4)
            elif action == "stop":
                bot.stop_movement()
        except Exception as e:
            print("⚠️ movement error:", e)

    print("🎯 Show a RED ball/object. Press q to quit.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            if FLIP_HORIZONTAL:
                frame = cv2.flip(frame, 1)
            frame = rotate_frame(frame, ROTATE_ANGLE)

            h, w = frame.shape[:2]
            center_x = w // 2

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            mask1 = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1)
            mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
            mask = cv2.bitwise_or(mask1, mask2)

            # cleanup
            mask = cv2.GaussianBlur(mask, (9, 9), 0)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                c = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(c)
                if area > MIN_AREA:
                    (x, y, w_box, h_box) = cv2.boundingRect(c)
                    cx = x + w_box // 2
                    # draw
                    cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, y + h_box // 2), 4, (255, 0, 0), -1)

                    # control logic
                    offset = (cx - center_x) / float(center_x)  # -1..1
                    if area >= CLOSE_AREA:
                        send("stop")
                        cv2.putText(frame, "CLOSE → STOP", (10, 30), 0, 0.7, (0, 0, 255), 2)
                    else:
                        if offset < -CENTER_TOLERANCE:
                            send("left")
                            cv2.putText(frame, "TURN LEFT", (10, 30), 0, 0.7, (0, 255, 255), 2)
                        elif offset > CENTER_TOLERANCE:
                            send("right")
                            cv2.putText(frame, "TURN RIGHT", (10, 30), 0, 0.7, (0, 255, 255), 2)
                        else:
                            send("forward")
                            cv2.putText(frame, "FORWARD", (10, 30), 0, 0.7, (0, 255, 0), 2)
                else:
                    send("stop")
                    cv2.putText(frame, "NO TARGET", (10, 30), 0, 0.7, (200, 200, 200), 2)
            else:
                send("stop")
                cv2.putText(frame, "NO TARGET", (10, 30), 0, 0.7, (200, 200, 200), 2)

            cv2.imshow("A1 Color Follower (RED)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        bot.stop_movement()
        cap.release()
        cv2.destroyAllWindows()
        bot.close()
        print("👋 Bye")

if __name__ == "__main__":
    main()
