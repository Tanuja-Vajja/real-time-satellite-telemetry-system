import socket
import threading
import os
import time
import struct
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# -------------------- CONFIGURATION --------------------
HOST = '127.0.0.1'
CHANNELS = {
    "Channel 1": {"port": 65439, "file": "sample1.txt"},
    "Channel 2": {"port": 65433, "file": "sample2.txt"}
}
SAVE_FOLDER = 'telemetry_logs'
os.makedirs(SAVE_FOLDER, exist_ok=True)

THRESHOLDS = {
    "battery_voltage": 3.3,
    "bus_current": 3000,
    "altitude": 500000.0,
    "pitch_error": 5.0,
    "roll_error": 5.0
}

# -------------------- DECODING FUNCTION --------------------
def decode_ccsds_256_frame(hex_data):
    try:
        raw = bytes.fromhex(hex_data)
        if len(raw) != 256:
            return f"Invalid frame size: {len(raw)} bytes", {}

        satellite_id = raw[0]
        orbit_number = int.from_bytes(raw[1:5], 'big')
        orbit_time = int.from_bytes(raw[5:13], 'big')
        mode = raw[13]
        battery_voltage = int.from_bytes(raw[14:16], 'big') / 1000.0
        bus_current = int.from_bytes(raw[16:18], 'big')
        altitude = struct.unpack('>f', raw[20:24])[0]
        pitch_error = struct.unpack('>f', raw[50:54])[0]
        roll_error = struct.unpack('>f', raw[54:58])[0]

        data = {
            "Satellite ID": satellite_id,
            "Orbit Number": orbit_number,
            "Orbit Time": orbit_time,
            "Mode": mode,
            "Battery Voltage": battery_voltage,
            "Bus Current": bus_current,
            "Altitude": altitude,
            "Pitch Error": pitch_error,
            "Roll Error": roll_error
        }

        return data, raw
    except Exception as e:
        return f"Error decoding frame: {e}", {}

# -------------------- SERVER SIMULATION --------------------
def start_server(channel_file, channel_port):
    def server_thread():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, channel_port))
            s.listen()
            conn, _ = s.accept()
            with conn, open(channel_file, 'r') as f:
                for line in f:
                    conn.sendall(line.strip().encode() + b'\n')
                    time.sleep(1)
                conn.sendall(b'__END__')

    threading.Thread(target=server_thread, daemon=True).start()

# -------------------- MAIN GUI CLASS --------------------
class TelemetryGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🚀 Advanced Satellite Telemetry System")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.channel_port = None
        self.channel_file = None
        self.frames = []
        self.running = False

        self.create_connect_screen()

    # -------------------- CONNECT SCREEN --------------------
    def create_connect_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        # Outer container frame (centered)
        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(expand=True, fill="both", padx=80, pady=80)

        # Title
        ctk.CTkLabel(
            frame,
            text="🛰️  Select Communication Channel",
            font=("Helvetica", 32, "bold"),
            text_color="#00e676"
        ).pack(pady=(80, 40))

        # Channel Dropdown
        self.channel_var = ctk.StringVar(value="Channel 1")
        dropdown = ctk.CTkOptionMenu(
            frame,
            variable=self.channel_var,
            values=list(CHANNELS.keys()),
            width=350,
            height=50,
            font=("Helvetica", 18),
            dropdown_font=("Helvetica", 16),
            fg_color="#2e7d32",
            button_color="#43a047",
            button_hover_color="#66bb6a"
        )
        dropdown.pack(pady=20)

        # Connect Button
        ctk.CTkButton(
            frame,
            text="Connect to Server",
            command=self.connect_to_server,
            width=350,
            height=60,
            font=("Helvetica", 20, "bold"),
            fg_color="#00897b",
            hover_color="#26a69a",
            corner_radius=12
        ).pack(pady=50)

        # Footer
        ctk.CTkLabel(
            frame,
            text="Developed by [Your Name] — Satellite Telemetry Interface",
            font=("Helvetica", 14),
            text_color="#b0bec5"
        ).pack(side="bottom", pady=20)

    # -------------------- DATA SCREEN --------------------
    def create_data_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", pady=5)

        ctk.CTkButton(top_frame, text="Disconnect", command=self.disconnect, fg_color="#D32F2F").pack(side="right", padx=10)
        ctk.CTkButton(top_frame, text="Back", command=self.create_connect_screen).pack(side="right")

        self.data_box = ctk.CTkTextbox(self, font=("Courier", 12), height=20)
        self.data_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)

        self.update_plot([], [])

    # -------------------- DATA & CHART --------------------
    def update_plot(self, altitudes, voltages):
        self.ax.clear()
        self.ax.plot(altitudes, label='Altitude (m)', color='orange', linewidth=2)
        self.ax.plot(voltages, label='Battery Voltage (V)', color='lime', linewidth=2)
        self.ax.set_title("Live Telemetry", fontsize=14)
        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.canvas.draw()

    def connect_to_server(self):
        channel_name = self.channel_var.get()
        self.channel_port = CHANNELS[channel_name]['port']
        self.channel_file = CHANNELS[channel_name]['file']
        start_server(self.channel_file, self.channel_port)
        self.create_data_screen()
        self.running = True
        threading.Thread(target=self.start_client, daemon=True).start()

    def start_client(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                client.connect((HOST, self.channel_port))
                buffer = b""
                altitudes, voltages = [], []

                while self.running:
                    data = client.recv(1024)
                    if not data:
                        break
                    buffer += data
                    if b'__END__' in buffer:
                        buffer = buffer.replace(b'__END__', b'')
                        break

                for line in buffer.decode().splitlines():
                    decoded, raw = decode_ccsds_256_frame(line)
                    if isinstance(decoded, dict):
                        ts = datetime.now().strftime("%H:%M:%S")

                        # ---- Vertical formatting ----
                        formatted = [f"{k}: {v}" for k, v in decoded.items()]
                        formatted_text = "\n".join(formatted)
                        text = f"[{ts}]\n{formatted_text}\n{'-'*70}\n"

                        # Display in GUI
                        self.data_box.insert("end", text)
                        self.data_box.see("end")

                        # Update chart
                        altitudes.append(decoded["Altitude"])
                        voltages.append(decoded["Battery Voltage"])
                        self.update_plot(altitudes, voltages)

                        # Save log
                        self.save_log(ts, formatted_text)
                        time.sleep(1)

        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def save_log(self, ts, content):
        filename = os.path.join(SAVE_FOLDER, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(filename, 'a') as f:
            f.write(f"[{ts}]\n{content}\n{'-'*70}\n")

    def disconnect(self):
        self.running = False
        messagebox.showinfo("Disconnected", "Connection closed.")
        self.create_connect_screen()

# -------------------- MAIN EXECUTION --------------------
if __name__ == "__main__":
    app = TelemetryGUI()
    app.mainloop()



