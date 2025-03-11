"""
This module implements a peer-to-peer (P2P) communication system.

Classes:
    Peer: Represents a single peer in the P2P network.
    Message: Represents a message to be sent between peers.
    Network: Manages the connections and message passing between peers.

Functions:
    connect_peers(peer1, peer2): Establishes a connection between two peers.
    send_message(sender, receiver, message): Sends a message from one peer to another.
    broadcast_message(sender, message): Sends a message from one peer to all connected peers.

Usage:
    - Create instances of the Peer class to represent nodes in the network.
    - Use the connect_peers function to establish connections between peers.
    - Use the send_message and broadcast_message functions to facilitate communication between peers.
"""

import os

class FileManager:
    def __init__(self , file_name , file_size , piece_size , peer_id):
        self.file_name = file_name
        self.file_size = file_size
        self.piece_size = piece_size
        self.peer_id = peer_id
        self.num_pieces = (file_size+piece_size-1) // piece_size
        self.storage_dir = f'peer_{peer_id}'

        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        
        print(f"Attempting to open file: {os.path.abspath(self.file_name)}")

    def split_file_into_pieces(self):

        try:
            with open(self.file_name, 'rb') as file:
                for i in range(self.num_pieces):
                    start_byte = i * self.piece_size
                    piece_data = file.read(self.piece_size)
                    self.save_piece(i, piece_data)
        except FileNotFoundError:
            print(f"File not found: {self.file_name}")
            raise

    def save_piece(self, piece_index, piece_data):
        piece_filename = os.path.join(self.storage_dir, f'piece_{piece_index}')
        with open(piece_filename, 'wb') as piece_file:
            piece_file.write(piece_data)

    def retrieve_piece(self, piece_index):
        piece_filename = os.path.join(self.storage_dir, f'piece_{piece_index}')
        with open(piece_filename, 'rb') as piece_file:
            return piece_file.read()
        return None
    
    def reassemble_file(self, output_file_name):
        with open(output_file_name, 'wb') as output_file:
            for i in range(self.num_pieces):
                piece_data = self.retrieve_piece(i)
                if piece_data:
                    output_file.write(piece_data)
                else:
                    print(f"Piece {i} is missing, can't reassemble file")
                    return False
        print(f"File reassembled successfully and saved as {output_file_name}")
        return True
    def is_piece_avalible(self, piece_index):
        piece_filename = os.path.join(self.storage_dir, f'piece_{piece_index}')
        return os.path.exists(piece_filename)
