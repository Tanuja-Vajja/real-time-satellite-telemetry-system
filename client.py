"""
Advanced Satellite Telemetry Visualization System (2-bit Frame Grid Version)
---------------------------------------------------------------------------
Each frame block now displays 2 binary digits for finer visualization.
"""

import sys
import socket
import struct
import time
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QStackedWidget, QHBoxLayout, QGridLayout,
    QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import pyqtgraph as pg

HOST = '127.0.0.1'
PORT = 65432
SAVE_FOLDER = 'telemetry_logs'
os.makedirs(SAVE_FOLDER, exist_ok=True)


# -----------------------------------------------------------
# Telemetry Frame Decoder
# -----------------------------------------------------------
def decode_ccsds_256_frame(hex_data):
    try:
        raw = bytes.fromhex(hex_data)
        if len(raw) != 256:
            return f"Invalid frame size: {len(raw)} bytes", {}

        data = {
            "Satellite ID": raw[0],
            "Orbit Number": int.from_bytes(raw[1:5], 'big'),
            "Orbit Time (UTC)": datetime.utcfromtimestamp(int.from_bytes(raw[5:13], 'big')).strftime('%Y-%m-%d %H:%M:%S'),
            "Battery Voltage": int.from_bytes(raw[14:16], 'big') / 1000.0,
            "Bus Current": int.from_bytes(raw[16:18], 'big'),
            "Altitude": struct.unpack('>f', raw[20:24])[0],
            "Pitch Error": struct.unpack('>f', raw[50:54])[0],
            "Roll Error": struct.unpack('>f', raw[54:58])[0],
        }

        readable = "\n".join([f"{k}: {v}" for k, v in data.items()])
        return readable, data, raw

    except Exception as e:
        return f"Error decoding frame: {e}", {}, b''


# -----------------------------------------------------------
# Background Client Thread
# -----------------------------------------------------------
class TelemetryClient(QThread):
    log_signal = pyqtSignal(str)
    data_signal = pyqtSignal(dict, bytes)
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                buffer = b""
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk
                    if b'__END__' in buffer:
                        buffer = buffer.replace(b'__END__', b'')
                        break

                for line in buffer.decode().splitlines():
                    decoded, frame_data, frame_bytes = decode_ccsds_256_frame(line)
                    self.log_signal.emit(decoded)
                    self.data_signal.emit(frame_data, frame_bytes)
                    time.sleep(1)

        except Exception as e:
            self.error_signal.emit(str(e))


# -----------------------------------------------------------
# Main GUI Application
# -----------------------------------------------------------
class TelemetryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛰 Satellite Telemetry Dashboard")
        self.setGeometry(200, 100, 1200, 850)
        self.frames = []
        self.data_points = {"Voltage": [], "Current": [], "Pitch": [], "Roll": []}

        # UI Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setStyleSheet(self.theme())
        self.init_connect_screen()
        self.init_data_screen()
        self.stack.setCurrentWidget(self.connect_widget)

    def theme(self):
        return """
            QWidget { background-color: #121212; color: #E0E0E0; font-family: 'Segoe UI'; }
            QPushButton { background-color: #0078d7; color: white; padding: 10px 18px; border-radius: 6px; font-size: 15px; font-weight: 600; }
            QPushButton:hover { background-color: #005a9e; }
            QTextEdit { background-color: #1f1f1f; border: 1px solid #333; border-radius: 6px; padding: 8px; font-size: 13px; }
            QComboBox { background-color: #1f1f1f; border: 1px solid #333; border-radius: 6px; padding: 6px; font-size: 14px; }
            QLabel { font-weight: 500; }
        """

    # ---------------- Connection Screen -----------------
    def init_connect_screen(self):
        self.connect_widget = QWidget()
        layout = QVBoxLayout()

        title = QLabel("🚀 Real-Time Satellite Telemetry System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 30px;
            font-weight: bold;
            color: #00bfff;
            font-family: 'Orbitron', 'Segoe UI Semibold';
            padding: 30px;
        """)
        layout.addWidget(title)

        sub = QLabel("Visualize • Decode • Analyze")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 18px; color: #cccccc; padding-bottom: 20px;")
        layout.addWidget(sub)

        label = QLabel("Select Communication Channel:")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 17px; font-weight: 600; padding: 10px; color: #e8e8e8;")

        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Channel 1", "Channel 2", "Channel 3"])
        self.channel_combo.setFixedWidth(300)
        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addWidget(self.channel_combo, alignment=Qt.AlignCenter)

        connect_btn = QPushButton("CONNECT TO SERVER")
        connect_btn.setFixedWidth(260)
        connect_btn.clicked.connect(self.connect_to_server)
        layout.addWidget(connect_btn, alignment=Qt.AlignCenter)
        layout.addStretch()

        self.connect_widget.setLayout(layout)
        self.stack.addWidget(self.connect_widget)

    # ---------------- Data Screen -----------------
    def init_data_screen(self):
        self.data_widget = QWidget()
        layout = QVBoxLayout()

        hbox = QHBoxLayout()
        self.status_label = QLabel("Status: Disconnected ❌")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")

        self.live_label = QLabel("●")
        self.live_label.setStyleSheet("color: gray; font-size: 18px;")

        decoded_btn = QPushButton("Decoded Data")
        decoded_btn.clicked.connect(self.show_decoded)
        graph_btn = QPushButton("Live Graphs")
        graph_btn.clicked.connect(self.show_graphs)
        grid_btn = QPushButton("Frame Grid")
        grid_btn.clicked.connect(self.show_frame_grid)
        back_btn = QPushButton("Back to Channel")
        back_btn.clicked.connect(self.go_back)

        hbox.addWidget(self.status_label)
        hbox.addWidget(self.live_label)
        hbox.addStretch()
        hbox.addWidget(decoded_btn)
        hbox.addWidget(graph_btn)
        hbox.addWidget(grid_btn)
        hbox.addWidget(back_btn)
        layout.addLayout(hbox)

        self.text_area = QTextEdit()
        layout.addWidget(self.text_area)

        # Graphs
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.graph_widget.setVisible(False)
        layout.addWidget(self.graph_widget)

        self.voltage_plot = self.graph_widget.addPlot(title="Battery Voltage (V)")
        self.voltage_curve = self.voltage_plot.plot(pen=pg.mkPen('g', width=2))
        self.graph_widget.nextRow()
        self.current_plot = self.graph_widget.addPlot(title="Bus Current (mA)")
        self.current_curve = self.current_plot.plot(pen=pg.mkPen('c', width=2))
        self.graph_widget.nextRow()
        self.pitch_plot = self.graph_widget.addPlot(title="Pitch & Roll Errors")
        self.pitch_curve = self.pitch_plot.plot(pen=pg.mkPen('y', width=2))
        self.roll_curve = self.pitch_plot.plot(pen=pg.mkPen('r', width=2))

        # Frame Grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setVisible(False)
        layout.addWidget(self.scroll)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll.setWidget(self.grid_container)

        self.data_widget.setLayout(layout)
        self.stack.addWidget(self.data_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start(1000)

    # ---------------- Event Handlers -----------------
    def connect_to_server(self):
        self.client = TelemetryClient()
        self.client.log_signal.connect(self.update_log)
        self.client.data_signal.connect(self.update_data)
        self.client.error_signal.connect(self.show_error)
        self.client.start()

        self.status_label.setText("Status: Connected ✅")
        self.status_label.setStyleSheet("color: #32cd32; font-weight: bold;")

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.toggle_live)
        self.blink_timer.start(500)
        self.stack.setCurrentWidget(self.data_widget)

    def go_back(self):
        reply = QMessageBox.question(
            self, "Return",
            "Go back to the channel selection screen?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.stack.setCurrentWidget(self.connect_widget)
            self.status_label.setText("Status: Disconnected ❌")
            self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            self.live_label.setStyleSheet("color: gray; font-size: 18px;")

    def toggle_live(self):
        color = "lime" if "gray" in self.live_label.styleSheet() else "gray"
        self.live_label.setStyleSheet(f"color: {color}; font-size: 18px;")

    def update_log(self, log):
        self.text_area.append(log)

    def update_data(self, data, frame_bytes):
        if not data:
            return
        self.frames.append(frame_bytes)
        self.data_points["Voltage"].append(data.get("Battery Voltage", 0))
        self.data_points["Current"].append(data.get("Bus Current", 0))
        self.data_points["Pitch"].append(data.get("Pitch Error", 0))
        self.data_points["Roll"].append(data.get("Roll Error", 0))
        if len(self.data_points["Voltage"]) > 50:
            for k in self.data_points:
                self.data_points[k] = self.data_points[k][-50:]

    def show_decoded(self):
        self.text_area.setVisible(True)
        self.graph_widget.setVisible(False)
        self.scroll.setVisible(False)

    def show_graphs(self):
        self.text_area.setVisible(False)
        self.graph_widget.setVisible(True)
        self.scroll.setVisible(False)

    def show_frame_grid(self):
        self.text_area.setVisible(False)
        self.graph_widget.setVisible(False)
        self.scroll.setVisible(True)
        self.display_latest_frame()

    # ---------------- Frame Grid (2-bit blocks) -----------------
    def display_latest_frame(self):
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if not self.frames:
            return
        frame_data = self.frames[-1]
        bits = ''.join(f'{b:08b}' for b in frame_data)
        row, col = 0, 0
        for i in range(0, len(bits), 2):  # each block = 2 bits
            lbl = QLabel(bits[i:i+2])
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background-color: #1f1f1f; border: 1px solid #333; border-radius: 3px;")
            lbl.setFixedSize(35, 28)
            self.grid_layout.addWidget(lbl, row, col)
            col += 1
            if col == 20:  # wrap grid
                col = 0
                row += 1

    def update_graphs(self):
        self.voltage_curve.setData(self.data_points["Voltage"])
        self.current_curve.setData(self.data_points["Current"])
        self.pitch_curve.setData(self.data_points["Pitch"])
        self.roll_curve.setData(self.data_points["Roll"])

    def show_error(self, msg):
        QMessageBox.critical(self, "Connection Error", msg)
        self.status_label.setText("Status: Disconnected ❌")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TelemetryApp()
    window.show()
    sys.exit(app.exec_())
