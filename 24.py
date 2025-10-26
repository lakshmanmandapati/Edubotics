import customtkinter as ctk
import threading
import speech_recognition as sr
from updated_bonicbot_controller import WebSocketBonicBotController

# === Connect to BonicBot ===
controller = WebSocketBonicBotController("10.177.152.30.", 8080)
controller.connect()

# === App Setup ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("BonicBot Voice Command Control")
app.geometry("500x250")

# === UI Components ===
instruction_label = ctk.CTkLabel(app, text="Speak commands: forward, backward, left, right, stop", font=("Arial", 14))
instruction_label.pack(pady=10)

status_label = ctk.CTkLabel(app, text="Status: Idle", font=("Arial", 14))
status_label.pack(pady=10)

command_label = ctk.CTkLabel(app, text="Last Command: None", font=("Arial", 14, "bold"))
command_label.pack(pady=10)

# === Speech Recognition Control ===
recognizer = sr.Recognizer()
mic = sr.Microphone()
listening_event = threading.Event()

def process_command(text):
    if "forward" in text:
        controller.move_forward(100)
    elif "backward" in text:
        controller.move_backward(100)
    elif "left" in text:
        controller.turn_left(100)
    elif "right" in text:
        controller.turn_right(100)
    elif "stop" in text:
        controller.stop_movement()
    else:
        status_label.configure(text="Unknown command")
        return
    status_label.configure(text=f"Command executed: {text}")
    command_label.configure(text=f"Last Command: {text}")

def listen_loop():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    while listening_event.is_set():
        with mic as source:
            status_label.configure(text="Listening...")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
                command = recognizer.recognize_google(audio).lower()
                process_command(command)
            except sr.WaitTimeoutError:
                status_label.configure(text="Listening timed out...")
            except sr.UnknownValueError:
                status_label.configure(text="Could not understand")
            except sr.RequestError:
                status_label.configure(text="Speech recognition service error")

def toggle_listening():
    if listening_event.is_set():
        listening_event.clear()
        status_label.configure(text="Status: Idle")
        toggle_button.configure(text="🎤 Start Listening")
    else:
        listening_event.set()
        threading.Thread(target=listen_loop, daemon=True).start()
        toggle_button.configure(text="⏹ Stop Listening")

# === Start/Stop Button ===
toggle_button = ctk.CTkButton(app, text="🎤 Start Listening", command=toggle_listening, width=200)
toggle_button.pack(pady=20)

app.mainloop()
