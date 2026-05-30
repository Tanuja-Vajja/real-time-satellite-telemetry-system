import struct
import random
from datetime import datetime
import os

def generate_random_frame():
    frame = bytearray(256)

    frame[0] = random.randint(1, 255)
    frame[1:5] = random.randint(1000, 99999).to_bytes(4, 'big')

    orbit_time = int(datetime.utcnow().timestamp())
    frame[5:13] = orbit_time.to_bytes(8, 'big')

    frame[13] = random.randint(0, 5)
    frame[14:16] = int(random.uniform(3.3, 4.2) * 1000).to_bytes(2, 'big')
    frame[16:18] = random.randint(100, 500).to_bytes(2, 'big')
    frame[18:20] = random.randint(0, 255).to_bytes(2, 'big')

    frame[20:24] = struct.pack('>f', random.uniform(400000, 500000))
    frame[24:28] = struct.pack('>f', random.uniform(-90, 90))
    frame[28:32] = struct.pack('>f', random.uniform(-180, 180))
    frame[32:34] = random.randint(0, 1000).to_bytes(2, 'big')
    frame[34] = random.getrandbits(8)
    frame[35:37] = random.randint(0, 5000).to_bytes(2, 'big')
    frame[37:39] = random.randint(0, 1000).to_bytes(2, 'big')
    frame[39:42] = bytes([random.getrandbits(8) for _ in range(3)])

    for i in range(4):
        temp = int(random.uniform(-20, 60) * 100)
        frame[42 + i * 2: 44 + i * 2] = struct.pack('>h', temp)

    frame[50:54] = struct.pack('>f', random.uniform(-5.0, 5.0))
    frame[54:58] = struct.pack('>f', random.uniform(-5.0, 5.0))

    return frame.hex()


def generate_sample_file(filename="sample.txt", frame_count=5):
    with open(filename, "w") as f:
        for _ in range(frame_count):
            hex_frame = generate_random_frame()
            f.write(hex_frame + "\n")

    print(f"Generated {frame_count} sample frames in '{filename}'.")


if __name__ == "__main__":
    generate_sample_file()
