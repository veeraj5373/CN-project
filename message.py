
"""
This module implements a simple peer-to-peer network using sockets and threading.
Functions:
    handle_client(client_socket):
        Handles incoming messages from a connected client socket.
    start_server(port):
        Starts a server that listens for incoming connections on the specified port.
    connect_to_server(ip, port):
        Connects to a server at the specified IP address and port, allowing the user to send messages.
Usage:
    Run the script and choose whether to start a server or connect to an existing server.
    If starting a server, provide the port number to listen on.
    If connecting to a server, provide the server's IP address and port number.
"""

import struct
import socket

# Define message types
CHOKE = 0
UNCHOKE = 1
INTERESTED = 2
NOT_INTERESTED = 3
HAVE = 4
BITFIELD = 5
REQUEST = 6
PIECE = 7
HANDSHAKE = 8  # Custom type for handshake

HANDSHAKE_HEADER = b"P2PFILESHARINGPROJ"  # 18-byte handshake header
ZERO_BITS = b"\x00" * 10  # 10-byte zero padding


class MessageHandler:
    def __init__(self, socket):
        """Initializes the MessageHandler with a socket."""
        self.socket = socket

    def send_message(self, msg_type, payload=b""):
        """Sends a message with the given type and optional payload."""
        length = 1 + len(payload)  # Message type + payload
        message = struct.pack(">I", length) + struct.pack(">B", msg_type) + payload
        self.socket.sendall(message)

    def receive_message(self):
        """Receives a message from the peer and extracts its type and payload."""
        try:
            length_data = self.socket.recv(4)  # Read 4-byte length
            if not length_data:
                return None, None

            length = struct.unpack(">I", length_data)[0]
            msg_type_data = self.socket.recv(1)  # Read 1-byte type
            msg_type = struct.unpack(">B", msg_type_data)[0]
            payload = self.socket.recv(length - 1) if length > 1 else b""

            return msg_type, payload
        except:
            return None, None

    def send_handshake(self, peer_id):
        """Sends a 32-byte handshake message."""
        peer_id_bytes = struct.pack(">I", peer_id)  # Convert peer_id to 4 bytes
        handshake_msg = HANDSHAKE_HEADER + ZERO_BITS + peer_id_bytes
        self.socket.sendall(handshake_msg)
        print(f"Handshake sent by Peer {peer_id}")

    def receive_handshake(self):
        """Receives and validates a handshake message."""
        expected_length = 32  # 18-byte header + 10-byte zeros + 4-byte peer_id
        received_data = self.socket.recv(expected_length)

        if len(received_data) == expected_length and received_data[:18] == HANDSHAKE_HEADER:
            received_peer_id = struct.unpack(">I", received_data[28:])[0]
            print(f"Handshake received from Peer {received_peer_id}")
            return received_peer_id
        else:
            print("Invalid handshake received.")
            return None

    def send_bitfield(self, bitfield):
        """Sends a bitfield message indicating available file pieces."""
        self.send_message(BITFIELD, bitfield)
        print(f"Sent bitfield: {bitfield}")

    def send_interested(self):
        """Sends an Interested message to a peer."""
        self.send_message(INTERESTED)
        print("Sent Interested message.")

    def send_not_interested(self):
        """Sends a Not Interested message to a peer."""
        self.send_message(NOT_INTERESTED)
        print("Sent Not Interested message.")

    def send_have(self, piece_index):
        """Sends a Have message to notify peers about a new piece."""
        payload = struct.pack(">I", piece_index)  # Convert piece index to 4 bytes
        self.send_message(HAVE, payload)
        print(f"Sent Have message for piece {piece_index}.")

    def send_request(self, piece_index):
        """Sends a Request message asking for a specific piece."""
        payload = struct.pack(">I", piece_index)
        self.send_message(REQUEST, payload)
        print(f"Sent Request message for piece {piece_index}.")

    def send_piece(self, piece_index, data):
        """Sends a Piece message containing the requested piece data."""
        payload = struct.pack(">I", piece_index) + data
        self.send_message(PIECE, payload)
        print(f"Sent Piece message for piece {piece_index}.")
