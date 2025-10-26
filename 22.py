import customtkinter as ctk
from updated_bonicbot_controller import WebSocketBonicBotController

# Connect to robot
controller = WebSocketBonicBotController("10.177.152.30", 8080)
controller.connect()

# GUI setup
app = ctk.CTk()
app.title("BonicBot A1 - Dual Hand Control")
app.geometry("600x700")

# === Functions ===
def update_right_arm(val=None):
    controller.control_right_shoulder_pitch(right_pitch_slider.get(), speed=700, acc=80)
    controller.control_right_elbow(right_elbow_slider.get(), speed=700, acc=80)
    controller.control_right_gripper(right_gripper_slider.get(), speed=700, acc=80)

    right_status_label.configure(
        text=f"Right Arm → Pitch: {right_pitch_slider.get()}°, "
             f"Elbow: {right_elbow_slider.get()}°, "
             f"Gripper: {right_gripper_slider.get()}°"
    )

def reset_right_arm():
    right_pitch_slider.set(0)
    right_elbow_slider.set(0)
    right_gripper_slider.set(0)
    update_right_arm()

def update_left_arm(val=None):
    controller.control_left_shoulder_pitch(left_pitch_slider.get(), speed=700, acc=80)
    controller.control_left_elbow(left_elbow_slider.get(), speed=700, acc=80)
    controller.control_left_gripper(left_gripper_slider.get(), speed=700, acc=80)

    left_status_label.configure(
        text=f"Left Arm → Pitch: {left_pitch_slider.get()}°, "
             f"Elbow: {left_elbow_slider.get()}°, "
             f"Gripper: {left_gripper_slider.get()}°"
    )

def reset_left_arm():
    left_pitch_slider.set(0)
    left_elbow_slider.set(0)
    left_gripper_slider.set(0)
    update_left_arm()

# === Right Arm Controls ===
ctk.CTkLabel(app, text="Right Arm Control", font=("Arial", 16, "bold")).pack(pady=10)

ctk.CTkLabel(app, text="Right Shoulder Pitch").pack(pady=(5, 0))
right_pitch_slider = ctk.CTkSlider(app, from_=-45, to=90, command=update_right_arm)
right_pitch_slider.set(0)
right_pitch_slider.pack(pady=(0, 10))

ctk.CTkLabel(app, text="Right Elbow").pack(pady=(5, 0))
right_elbow_slider = ctk.CTkSlider(app, from_=-90, to=0, command=update_right_arm)
right_elbow_slider.set(0)
right_elbow_slider.pack(pady=(0, 10))

ctk.CTkLabel(app, text="Right Gripper").pack(pady=(5, 0))
right_gripper_slider = ctk.CTkSlider(app, from_=-45, to=45, command=update_right_arm)
right_gripper_slider.set(0)
right_gripper_slider.pack(pady=(0, 10))

right_reset_button = ctk.CTkButton(app, text="↩️ Reset Right Arm", command=reset_right_arm, width=200)
right_reset_button.pack(pady=10)

right_status_label = ctk.CTkLabel(app, text="Right Arm Ready", font=("Arial", 12))
right_status_label.pack(pady=5)

# === Left Arm Controls ===
ctk.CTkLabel(app, text="Left Arm Control", font=("Arial", 16, "bold")).pack(pady=10)

ctk.CTkLabel(app, text="Left Shoulder Pitch").pack(pady=(5, 0))
left_pitch_slider = ctk.CTkSlider(app, from_=-45, to=90, command=update_left_arm)
left_pitch_slider.set(0)
left_pitch_slider.pack(pady=(0, 10))

ctk.CTkLabel(app, text="Left Elbow").pack(pady=(5, 0))
left_elbow_slider = ctk.CTkSlider(app, from_=-90, to=0, command=update_left_arm)
left_elbow_slider.set(0)
left_elbow_slider.pack(pady=(0, 10))

ctk.CTkLabel(app, text="Left Gripper").pack(pady=(5, 0))
left_gripper_slider = ctk.CTkSlider(app, from_=-45, to=45, command=update_left_arm)
left_gripper_slider.set(0)
left_gripper_slider.pack(pady=(0, 10))

left_reset_button = ctk.CTkButton(app, text="↩️ Reset Left Arm", command=reset_left_arm, width=200)
left_reset_button.pack(pady=10)

left_status_label = ctk.CTkLabel(app, text="Left Arm Ready", font=("Arial", 12))
left_status_label.pack(pady=5)

app.mainloop()

