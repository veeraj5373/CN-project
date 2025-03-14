import sys
import socket
import threading

class Peer:
    def __init__(self, peer_id, host="localhost", port=None):
        self.peer_id = peer_id
        self.host = host
        self.port = port if port else 7000 + peer_id  # Assign port dynamically
        self.connections = []
        print(f"Peer {self.peer_id} initialized on port {self.port}")

    def start_server(self):
        """ Starts a server socket to accept connections from peers. """
        print(f"Peer {self.peer_id} is listening on port {self.port}...")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection received from {addr}")
            self.connections.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def connect_to_peer(self, peer_host, peer_port):
        """ Connects to an existing peer. """
        print(f"Peer {self.peer_id} attempting to connect to previous peers at {peer_host}:{peer_port}...")
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_host, peer_port))
            self.connections.append(peer_socket)
            print(f"Connected to Peer at {peer_host}:{peer_port}")
        except Exception as e:
            print(f"Connection failed: {e}")

    def handle_client(self, client_socket):
        """ Handles incoming messages from a connected peer. """
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"Received: {message}")
            except:
                break
        client_socket.close()

    def send_message(self, message):
        """ Sends a message to all connected peers. """
        if not self.connections:
            print("No active connections to send messages.")
            return

        print(f"Peer {self.peer_id} sending message: {message}")
        for conn in self.connections:
            try:
                conn.sendall(message.encode())
            except Exception as e:
                print(f"Error sending message: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing peer ID argument.")
        sys.exit(1)

    peer_id = int(sys.argv[1])
    peer = Peer(peer_id)

    # Start the server thread
    threading.Thread(target=peer.start_server, daemon=True).start()

    # Connect to previous peers (Example: 1002 connects to 1001)
    if peer_id > 1001:
        peer.connect_to_peer("localhost", 7000 + (peer_id - 1))

    while True:
        print(f"Peer {peer_id} waiting for input...")
        msg = input(f"Peer {peer_id}, type message: ").strip()
        
        if msg:  # Only send if message is not empty
            peer.send_message(msg)
