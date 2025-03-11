"""
This module implements a peer-to-peer communication system.

The main functionalities provided by this module include:
- Establishing connections between peers
- Sending and receiving messages between peers
- Handling peer disconnections and reconnections
- Managing peer-to-peer network topology

Usage:
- Initialize the peer-to-peer network
- Connect to other peers
- Send and receive messages
- Handle network events such as peer disconnections

This module is designed to facilitate decentralized communication between nodes in a network.
"""

import configparser


class Config:
    def __init__(self, common_config_path="Common.cfg", peer_info_config_path="PeerInfo.cfg"):
        self.common_config = self.parse_common_config(common_config_path)
        self.peer_info = self.parse_peer_info(peer_info_config_path)

    def parse_common_config(self, common_config_path):
        """Parses the Common.cfg file and returns the configuration as a dictionary."""
        common_config = {}
        with open(common_config_path, 'r') as file:
            for line in file:
                if line.strip():  # Ignore empty lines
                    key, value = line.strip().split()
                    if key in ['NumberOfPreferredNeighbors', 'UnchokingInterval', 'OptimisticUnchokingInterval', 'FileSize', 'PieceSize']:
                        common_config[key] = int(value)  # Convert to integer
                    else:
                        common_config[key] = value  # Keep as string for others
        return common_config

    def parse_peer_info(self, peer_config_path):
        """Parses the PeerInfo.cfg file and returns a list of peer dictionaries."""
        peer_info = []
        with open(peer_config_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                peer_id = int(parts[0])
                host = parts[1]
                port = int(parts[2])
                has_file = bool(int(parts[3]))  # Convert to boolean (True or False)
                peer_info.append({
                    'peer_id': peer_id,
                    'host': host,
                    'port': port,
                    'has_file': has_file
                })
        return peer_info

    def get_common_config(self):
        """Returns the parsed common configuration."""
        return self.common_config
    
    def get_peer_config(self):
        """Returns the list of parsed peer information."""
        return self.peer_info
    
    def get_peer_info(self, peer_id):
        """Returns the specific peer's information based on the peer_id."""
        for peer in self.peer_info:
            if peer['peer_id'] == peer_id:
                return peer
        return None  # Return None if the peer ID is not found

    