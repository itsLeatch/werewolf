import socket

HOST = "localhost"  # The server's hostname or IP address
PORT = 28830  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        #recive a message and print it only if it is not empty
        data = s.recv(1024)
        if data != b'':
            print("Received", repr(data))
        