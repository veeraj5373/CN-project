"""
This Python file is designed to perform the following tasks:

1. Import necessary libraries and modules.
2. Define functions and classes required for the main functionality.
3. Implement the main logic of the program, including data processing and manipulation.
4. Handle user inputs and outputs, if applicable.
5. Include error handling and logging mechanisms to ensure robustness.
6. Provide unit tests or examples to demonstrate the usage of the implemented functions and classes.
"""

import logging
import os
from datetime import datetime

class PeerLogger:
    def __init__(self, peer_id):
        """
        Initialize the logger for a specific peer.
        Creates a log file with the name 'log_peer_[peerID].log'.
        """
        self.peer_id = peer_id
        log_filename = f'log_peer_{peer_id}.log'

        # Create a logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Set up the logging configuration
        logging.basicConfig(
            filename=os.path.join('logs', log_filename),
            filemode='a',
            format='%(message)s',
            level=logging.INFO
        )

    def _log(self, message):
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"[{current_time}] {message}")

    def log_tcp_connection(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} makes a connection to Peer {peer_id_2}.")

    def log_tcp_connected(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} is connected from Peer {peer_id_2}.")

    def log_preferred_neighbors(self, preferred_neighbors):
        
        preferred_neighbors_str = ", ".join(map(str, preferred_neighbors))
        self._log(f"Peer {self.peer_id} has the preferred neighbors [{preferred_neighbors_str}].")

    def log_optimistically_unchoked(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} has the optimistically unchoked neighbor {peer_id_2}.")

    def log_unchoked(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} is unchoked by Peer {peer_id_2}.")

    def log_choked(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} is choked by Peer {peer_id_2}.")

    def log_have(self, peer_id_2, piece_index):
        
        self._log(f"Peer {self.peer_id} received the 'have' message from Peer {peer_id_2} for the piece {piece_index}.")

    def log_interested(self, peer_id_2):
        
        self._log(f"Peer {self.peer_id} received the 'interested' message from Peer {peer_id_2}.")

    def log_not_interested(self, peer_id_2):
      
        self._log(f"Peer {self.peer_id} received the 'not interested' message from Peer {peer_id_2}.")

    def log_piece_downloaded(self, peer_id_2, piece_index, num_pieces):
       
        self._log(f"Peer {self.peer_id} has downloaded the piece {piece_index} from Peer {peer_id_2}. Now the number of pieces it has is {num_pieces}.")

    def log_complete_file_downloaded(self):
    
        self._log(f"Peer {self.peer_id} has downloaded the complete file.")
