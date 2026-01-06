
import socket
HOST = "localhost"  # Standard loopback interface address (localhost)
PORT = 28830  # Port to listen on (non-privileged ports are > 1023)

numberOfPlayers = int(input("Enter number of players: "))
playerConnections = []
for i in range(numberOfPlayers):
    print(f"Waiting for player {i+1} to connect...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        playerConnections.append(conn)
        with conn:
            print(f"Connected by {addr}")

for player in playerConnections:
    player.sendall("Hi")