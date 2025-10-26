import customtkinter as ctk
from updated_bonicbot_controller import WebSocketBonicBotController

# === Connect to the robot ===
controller = WebSocketBonicBotController("10.177.152.30", 8080)
controller.connect()

# === GUI Setup ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("BonicBot A1 - Head Pan Control")
app.geometry("400x300")

# === Functions ===
def update_head(val=None):
    pan = round(pan_slider.get(), 1)
    controller.control_head(pan_angle=pan)   # only pan for A1
    pan_value_label.configure(text=f"{pan}°")
    status_label.configure(text=f"Moved head to Pan: {pan}°")

def reset_head():
    pan_slider.set(0)
    update_head()

def preset_head(pan):
    pan_slider.set(pan)
    update_head()

# === Pan Control Frame ===
pan_frame = ctk.CTkFrame(app)
pan_frame.pack(pady=20, fill="x", padx=20)

ctk.CTkLabel(pan_frame, text="Pan (Left / Right)").grid(row=0, column=0, padx=5, pady=5)
pan_slider = ctk.CTkSlider(pan_frame, from_=-90, to=90, command=update_head)
pan_slider.set(0)
pan_slider.grid(row=0, column=1, sticky="ew", padx=5)
pan_value_label = ctk.CTkLabel(pan_frame, text="0°")
pan_value_label.grid(row=0, column=2, padx=5)

# === Preset Buttons Frame ===
preset_frame = ctk.CTkFrame(app)
preset_frame.pack(pady=15, fill="x", padx=20)

ctk.CTkButton(preset_frame, text="Center", command=reset_head).grid(row=0, column=0, padx=5, pady=5)
ctk.CTkButton(preset_frame, text="Look Left", command=lambda: preset_head(-45)).grid(row=0, column=1, padx=5, pady=5)
ctk.CTkButton(preset_frame, text="Look Right", command=lambda: preset_head(45)).grid(row=0, column=2, padx=5, pady=5)

# === Status Label ===
status_label = ctk.CTkLabel(app, text="Ready", font=("Arial", 14))
status_label.pack(pady=10)

app.mainloop()
