import socket
import time

HOST = '127.0.0.1'
PORT = 65432
SAMPLE_FILE = 'sample.txt'


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Server listening on", HOST, PORT)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            with open(SAMPLE_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        conn.sendall(line.encode() + b'\n')
                        time.sleep(1)
            conn.sendall(b'__END__')


if __name__ == "__main__":
    start_server()
