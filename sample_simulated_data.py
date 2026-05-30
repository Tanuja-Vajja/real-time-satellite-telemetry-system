import random
import struct

def generate_random_frame():
    frame = bytearray(256)
    frame[0] = random.randint(1, 255)  # Satellite ID
    frame[1:5] = random.randint(1, 99999).to_bytes(4, 'big')  # Orbit Number
    frame[5:13] = random.randint(1000000, 99999999).to_bytes(8, 'big')  # Orbit Time
    frame[13] = random.randint(0, 5)  # Mode
    frame[14:16] = int(random.uniform(3.2, 4.2) * 1000).to_bytes(2, 'big')  # Battery Voltage
    frame[16:18] = random.randint(1000, 4000).to_bytes(2, 'big')  # Bus Current
    frame[18:20] = random.randint(0, 100).to_bytes(2, 'big')  # Command
    frame[20:24] = struct.pack('>f', random.uniform(300000, 700000))  # Altitude
    frame[24:28] = struct.pack('>f', random.uniform(-90, 90))  # Latitude
    frame[28:32] = struct.pack('>f', random.uniform(-180, 180))  # Longitude
    frame[32:34] = random.randint(100, 300).to_bytes(2, 'big')  # Solar Array Current
    frame[34] = random.randint(0, 255)  # Heaters State (8 bits)
    frame[35:37] = random.randint(0, 500).to_bytes(2, 'big')  # OB Command Count
    frame[37:39] = random.randint(0, 500).to_bytes(2, 'big')  # Attitude Count
    for i in range(3):  # Reaction Wheels
        frame[39+i] = random.randint(0, 255)
    for i in range(4):  # Thermistors
        temp = int(random.uniform(20.0, 60.0) * 100)
        frame[42 + i*2 : 44 + i*2] = struct.pack('>h', temp)
    frame[50:54] = struct.pack('>f', random.uniform(-5.0, 5.0))  # Pitch Error
    frame[54:58] = struct.pack('>f', random.uniform(-5.0, 5.0))  # Roll Error
    return frame.hex()

def generate_sample_file(filename, frame_count=5):
    with open(filename, "w") as f:
        for _ in range(frame_count):
            f.write(generate_random_frame() + "\n")
    print(f"{filename} created with {frame_count} frames.")

if __name__ == "__main__":
    generate_sample_file("sample1.txt", frame_count=10)
    generate_sample_file("sample2.txt", frame_count=10)
