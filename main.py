import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import speech_recognition as sr
import threading
import time
try:
    from plyer import vibrator
except ImportError:
    vibrator = None

# -------------------------------
# Keywords
# -------------------------------
EMERGENCY_KEYWORDS = ["fire", "help", "danger", "alarm", "look out", "emergency", "this is not a drill"]
NAME_WORDS = ["mom", "dad", "sister", "brother", "friend", "Emily"]
TIME_WORDS = ["tomorrow", "monday", "soon", "later", "tonight"]

listening = False

# -------------------------------
# Main Window Setup
# -------------------------------
root = tk.Tk()
root.title("ClearConnect - Live Captions + Alerts")
root.geometry("1000x600")
root.minsize(900, 500)  # minimum size
root.config(bg="#e0e0e0")  # light gray background

# Use grid for responsiveness
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=3)  # left frame
root.grid_columnconfigure(1, weight=1)  # right frame

# -------------------------------
# LEFT FRAME (Captions)
# -------------------------------
left_frame = tk.Frame(root, bd=2, relief="groove", padx=10, pady=10, bg="#f7f7f7")
left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

left_frame.grid_rowconfigure(3, weight=1)  # captions box expands
left_frame.grid_columnconfigure(0, weight=1)

tk.Label(left_frame, text="LIVE CAPTIONS", font=("Arial", 16, "bold"), bg="#f7f7f7", fg="#333333").grid(row=0, column=0, sticky="w")
tk.Label(left_frame, text="🎤 Listening...", font=("Arial", 12), bg="#f7f7f7").grid(row=1, column=0, sticky="w", pady=5)
speaker_label = tk.Label(left_frame, text="Speaker Detected: John", font=("Arial", 12), bg="#f7f7f7")
speaker_label.grid(row=2, column=0, sticky="w")

caption_box = scrolledtext.ScrolledText(left_frame, font=("Arial", 12), wrap="word", bg="#ffffff")
caption_box.grid(row=3, column=0, sticky="nsew", pady=5)

# -------------------------------
# RIGHT FRAME (Alerts & Buttons)
# -------------------------------
right_frame = tk.Frame(root, bd=2, relief="groove", padx=10, pady=10, bg="#f7f7f7")
right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

right_frame.grid_rowconfigure(9, weight=1)  # last row stretches
right_frame.grid_columnconfigure(0, weight=1)

tk.Label(right_frame, text="ALERTS & NOTIFICATIONS", font=("Arial", 16, "bold"), bg="#f7f7f7", fg="#333333").grid(row=0, column=0, pady=5)

alert_label = tk.Label(right_frame, text="No alerts", bg="#d9d9d9", font=("Arial", 14), width=25, height=3, relief="sunken")
alert_label.grid(row=1, column=0, pady=10, sticky="ew")

tk.Checkbutton(right_frame, text="Incoming Call\nVisual: ON   Vibration: ON", bg="#f7f7f7").grid(row=2, column=0, sticky="w", pady=3)
tk.Checkbutton(right_frame, text="Emergency Alert\nScreen: RED   Vibration: STRONG", bg="#f7f7f7").grid(row=3, column=0, sticky="w", pady=3)
tk.Checkbutton(right_frame, text="Name Called\nIcon + Text   Short Vibration", bg="#f7f7f7").grid(row=4, column=0, sticky="w", pady=3)

tk.Label(right_frame, text="Customize Alerts", font=("Arial", 12, "bold"), bg="#f7f7f7").grid(row=5, column=0, pady=10)

# -------------------------------
# Helper functions
# -------------------------------
def flash_button(btn, color="yellow", duration=500):
    original_bg = btn.cget("bg")
    btn.config(bg=color)
    root.after(duration, lambda: btn.config(bg=original_bg))

def display_caption(text):
    caption_box.configure(state="normal")
    start_index = caption_box.index(tk.END)
    caption_box.insert(tk.END, text + "\n")

    for word in EMERGENCY_KEYWORDS:
        idx = start_index
        while True:
            idx = caption_box.search(word, idx, nocase=1, stopindex=tk.END)
            if not idx: break
            end_idx = f"{idx}+{len(word)}c"
            caption_box.tag_add("emergency", idx, end_idx)
            idx = end_idx

    for word in NAME_WORDS:
        idx = start_index
        while True:
            idx = caption_box.search(word, idx, nocase=1, stopindex=tk.END)
            if not idx: break
            end_idx = f"{idx}+{len(word)}c"
            caption_box.tag_add("name", idx, end_idx)
            idx = end_idx

    for word in TIME_WORDS:
        idx = start_index
        while True:
            idx = caption_box.search(word, idx, nocase=1, stopindex=tk.END)
            if not idx: break
            end_idx = f"{idx}+{len(word)}c"
            caption_box.tag_add("time", idx, end_idx)
            idx = end_idx

    caption_box.tag_config("emergency", foreground="#ff0000", font=("Arial", 12, "bold"))
    caption_box.tag_config("name", foreground="#0077ff", font=("Arial", 12, "bold"))
    caption_box.tag_config("time", foreground="#00aa00", font=("Arial", 12, "bold"))
    caption_box.see(tk.END)
    caption_box.configure(state="disabled")

def flash_alert():
    alert_label.config(bg="#ff6666")
    root.after(500, lambda: alert_label.config(bg="#d9d9d9"))

def check_keywords(text):
    lower_text = text.lower()
    for word in EMERGENCY_KEYWORDS:
        if word in lower_text:
            alert_label.config(text=f"🚨 EMERGENCY: {word.upper()}!")
            flash_alert()
            flash_button(fire_btn, color="#ff3333")
            return
    for word in NAME_WORDS:
        if word in lower_text:
            alert_label.config(text=f"👤 Name Mentioned: {word}")
            return
    for word in TIME_WORDS:
        if word in lower_text:
            alert_label.config(text=f"⏰ Time Reference: {word}")
            return
    alert_label.config(text="No alerts")

# -------------------------------
# Speech Recognition
# -------------------------------
def listen_loop():
    global listening
    recognizer = sr.Recognizer()
    try:
        microphone = sr.Microphone()
    except OSError:
        display_caption("[Error: No microphone found]")
        return
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    while listening:
        try:
            with microphone as source:
                audio = recognizer.listen(source, phrase_time_limit=5)
            text = recognizer.recognize_google(audio)
            display_caption("You said: " + text)
            check_keywords(text)
        except sr.UnknownValueError:
            display_caption("[Could not understand audio]")
        except sr.RequestError:
            display_caption("[Speech service unavailable]")
        except Exception as e:
            display_caption(f"[Error: {e}]")

# -------------------------------
# Button Actions
# -------------------------------
def start_listening():
    global listening
    listening = True
    thread = threading.Thread(target=listen_loop)
    thread.daemon = True
    thread.start()

def stop_listening():
    global listening
    listening = False
    alert_label.config(text="No alerts")

def edit_patterns():
    global EMERGENCY_KEYWORDS
    new_patterns = simpledialog.askstring("Edit Emergency Keywords",
                                           "Enter emergency keywords separated by commas:",
                                           initialvalue=",".join(EMERGENCY_KEYWORDS))
    if new_patterns:
        EMERGENCY_KEYWORDS = [word.strip() for word in new_patterns.split(",")]
        messagebox.showinfo("Updated", f"Emergency keywords updated:\n{', '.join(EMERGENCY_KEYWORDS)}")

def test_doorbell():
    alert_label.config(text="🔔 Doorbell Detected!")
    flash_button(doorbell_btn, color="#ffcc00")
    if vibrator:
        vibrator.vibrate(0.5)

def test_emergency():
    alert_label.config(text="🚨 Fire Alarm Detected!")
    flash_button(fire_btn, color="#ff3333")
    if vibrator:
        vibrator.vibrate(1)

def test_vibration():
    flash_button(test_vib_btn, color="#33ccff")
    if vibrator:
        vibrator.vibrate(1)
    else:
        messagebox.showinfo("Vibration", "Simulated vibration triggered!")

# -------------------------------
# Buttons Frame (Left)
# -------------------------------
button_frame = tk.Frame(left_frame, bg="#f7f7f7")
button_frame.grid(row=4, column=0, pady=10, sticky="ew")
button_frame.grid_columnconfigure((0,1), weight=1)

start_btn = tk.Button(button_frame, text="Start Listening", bg="#33cc66", fg="white", font=("Arial", 12), command=start_listening)
start_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

stop_btn = tk.Button(button_frame, text="Stop Listening", bg="#ff4444", fg="white", font=("Arial", 12), command=stop_listening)
stop_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

doorbell_btn = tk.Button(button_frame, text="Test Doorbell Alert", bg="#ffcc00", font=("Arial", 12), command=test_doorbell)
doorbell_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

fire_btn = tk.Button(button_frame, text="Test Emergency Alarm", bg="#ff3333", fg="white", font=("Arial", 12), command=test_emergency)
fire_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

# -------------------------------
# Buttons Frame (Right)
# -------------------------------
edit_patterns_btn = tk.Button(right_frame, text="Edit Patterns", bg="#3399ff", fg="white", font=("Arial", 12), command=edit_patterns)
edit_patterns_btn.grid(row=6, column=0, pady=5, sticky="ew")

test_vib_btn = tk.Button(right_frame, text="Test Vibration", bg="#33ccff", font=("Arial", 12), command=test_vibration)
test_vib_btn.grid(row=7, column=0, pady=5, sticky="ew")

# -------------------------------
# Run App
# -------------------------------
root.mainloop()
