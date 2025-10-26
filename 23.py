import customtkinter as ctk
from updated_bonicbot_controller import WebSocketBonicBotController

# Connect to robot
controller = WebSocketBonicBotController("10.177.152.30", 8080)
controller.connect()

# GUI setup
app = ctk.CTk(fg_color="#1e1e2f")   # Dark background
app.title("BonicBot A1 - Wheel Movement Control")
app.geometry("420x450")

# === Functions ===
def move_forward():
    controller.move_forward(20)
    status_label.configure(text="Moving Forward ⮝")

def move_backward():
    controller.move_backward(20)
    status_label.configure(text="Moving Backward ⮟")

def turn_left():
    controller.turn_left(20)
    status_label.configure(text="Turning Left ⮜")

def turn_right():
    controller.turn_right(20)
    status_label.configure(text="Turning Right ⮞")

def stop():
    controller.stop_movement()
    status_label.configure(text="Stopped ⏺")

# === Frame for controls ===
frame = ctk.CTkFrame(app, corner_radius=15, fg_color="#2c2c40")  # Slightly lighter
frame.pack(pady=20, padx=20, fill="both", expand=True)

# Configure grid inside frame
frame.grid_rowconfigure((0,1,2,3), weight=1)
frame.grid_columnconfigure((0,1,2), weight=1)

# Title
title = ctk.CTkLabel(frame, text="Wheel Control", font=("Arial", 18, "bold"), text_color="white")
title.grid(row=0, column=1, pady=(10,20))

# Buttons in D-pad layout
forward_btn = ctk.CTkButton(frame, text="⮝", width=80, height=50, command=move_forward, fg_color="#4CAF50")
forward_btn.grid(row=1, column=1, pady=5)

left_btn = ctk.CTkButton(frame, text="⮜", width=80, height=50, command=turn_left, fg_color="#2196F3")
left_btn.grid(row=2, column=0, padx=5, pady=5)

stop_btn = ctk.CTkButton(frame, text="⏺ Stop", width=80, height=50, fg_color="red", hover_color="#b71c1c", command=stop)
stop_btn.grid(row=2, column=1, padx=5, pady=5)

right_btn = ctk.CTkButton(frame, text="⮞", width=80, height=50, command=turn_right, fg_color="#2196F3")
right_btn.grid(row=2, column=2, padx=5, pady=5)

backward_btn = ctk.CTkButton(frame, text="⮟", width=80, height=50, command=move_backward, fg_color="#FF9800")
backward_btn.grid(row=3, column=1, pady=5)

# Status label
status_label = ctk.CTkLabel(app, text="Ready", font=("Arial", 14), text_color="white")
status_label.pack(pady=15)

app.mainloop()
