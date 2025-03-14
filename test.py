# this is used for testing the code

### This is a test file to test the configuration class ###
# from config import Config

# def run_config_test():
#     # Initialize the configuration class (paths are already set in the config file)
#     config = Config()

#     # Get and print common configuration
#     common_config = config.get_common_config()
#     print("Common Configuration:")
#     for key, value in common_config.items():
#         print(f"{key}: {value}")
    
#     # Get and print peer information
#     peer_info = config.get_peer_config()
#     print("\nPeer Information:")
#     for peer in peer_info:
#         print(f"Peer ID: {peer['peer_id']}, Host: {peer['host']}, Port: {peer['port']}, Has File: {peer['has_file']}")
    
    
#     peer_id = 1001 
#     specific_peer_info = config.get_peer_info(peer_id)
#     if specific_peer_info:
#         print(f"\nSpecific Peer (ID {peer_id}) Information:")
#         for key, value in specific_peer_info.items():
#             print(f"{key}: {value}")
#     else:
#         print(f"\nPeer with ID {peer_id} not found.")

# if __name__ == "__main__":
#     run_config_test()

### This is a test file to test the file manager class ###

# from config import Config
# from file_manager import FileManager
# import os

# def test_file_manager():
#     # Initialize the configuration class
#     config = Config()

#     # Get and print common configuration
#     common_config = config.get_common_config()
#     print("Common Configuration:")
#     for key, value in common_config.items():
#         print(f"{key}: {value}")

#     # Get and print peer information
#     peer_info = config.get_peer_config()
#     print("\nPeer Information:")
#     for peer in peer_info:
#         print(f"Peer ID: {peer['peer_id']}, Host: {peer['host']}, Port: {peer['port']}, Has File: {peer['has_file']}")

#     # Identify the peer that has the full file
#     peer_id_with_file = None
#     for peer in peer_info:
#         if peer['has_file'] == 1:
#             peer_id_with_file = peer['peer_id']
#             break  # Stop once we find the peer with the file

#     if peer_id_with_file:
#         print(f"\nPeer with file (ID {peer_id_with_file}) found.")

#         # Get the file name and other common configurations
#         file_name = common_config['FileName']  # Just 'tree.jpg', file is in peer's folder
#         file_size = common_config['FileSize']
#         piece_size = common_config['PieceSize']

#         # Construct the full file path based on peer ID (e.g., /path/to/peer_1001/tree.jpg)
#         file_path = os.path.join(f"./{peer_id_with_file}", file_name)
        
#         # Ensure the file exists at the constructed path
#         if not os.path.exists(file_path):
#             print(f"Error: The file {file_path} does not exist.")
#             return

#         # Initialize the FileManager for this peer
#         file_manager = FileManager(file_path, file_size, piece_size, peer_id_with_file)

#         # Now call the split_file_into_pieces method to test the functionality
#         file_manager.split_file_into_pieces()

#         # Optionally, you can reassemble the file to test the reassemble logic as well
#         output_file_name = f"reassembled_{file_name.split('/')[-1]}"
#         file_manager.reassemble_file(output_file_name)

#     else:
#         print("No peer with the full file found.")

# if __name__ == "__main__":
#     test_file_manager()

### This is a test file to test the message class ###

# from message import Message
# import struct

# def test_handshake():
#     peer_id = 1001
#     handshake = Message.create_handshake_message(peer_id)
#     print(f"Generated Handshake: {handshake}")
    
#     parsed_peer_id = Message.parse_handshake_message(handshake)
#     assert parsed_peer_id == peer_id, f"Expected peer ID {peer_id}, got {parsed_peer_id}"
#     print("Handshake test passed.")

# def test_have_message():
#     piece_index = 4
#     have_message = Message.create_have_message(piece_index)
#     print(f"Generated 'Have' Message: {have_message}")

#     parsed_piece_index = Message.parse_have_message(have_message)
#     assert parsed_piece_index == piece_index, f"Expected piece index {piece_index}, got {parsed_piece_index}"
#     print("Have message test passed.")

# def test_bitfield_message():
#     bitfield = b'\xF0'  # Example bitfield: 11110000 in binary
#     bitfield_message = Message.create_bitfield_message(bitfield)
#     print(f"Generated Bitfield Message: {bitfield_message}")

#     parsed_bitfield = Message.parse_bitfield_message(bitfield_message)
#     assert parsed_bitfield == bitfield, f"Expected bitfield {bitfield}, got {parsed_bitfield}"
#     print("Bitfield message test passed.")

# def test_request_message():
#     piece_index = 10
#     request_message = Message.create_request_message(piece_index)
#     print(f"Generated 'Request' Message: {request_message}")

#     message_type, parsed_payload = Message.parse_actual_message(request_message)
#     assert message_type == Message.REQUEST, f"Expected message type {Message.REQUEST}, got {message_type}"
    
#     parsed_piece_index = struct.unpack('>I', parsed_payload)[0]
#     assert parsed_piece_index == piece_index, f"Expected piece index {piece_index}, got {parsed_piece_index}"
#     print("Request message test passed.")

# def test_piece_message():
#     piece_index = 3
#     piece_data = b'This is piece data'
#     piece_message = Message.create_piece_message(piece_index, piece_data)
#     print(f"Generated 'Piece' Message: {piece_message}")

#     parsed_piece_index, parsed_piece_data = Message.parse_piece_message(piece_message)
#     assert parsed_piece_index == piece_index, f"Expected piece index {piece_index}, got {parsed_piece_index}"
#     assert parsed_piece_data == piece_data, f"Expected piece data {piece_data}, got {parsed_piece_data}"
#     print("Piece message test passed.")

# if __name__ == '__main__':
#     test_handshake()
#     test_have_message()
#     test_bitfield_message()
#     test_request_message()
#     test_piece_message()

#     print("All tests passed!")

### This is a test file to test the logger class ###
# from logger import PeerLogger

# def test_logger():
#     peer_id = 1001
#     logger = PeerLogger(peer_id)

#     logger.log_tcp_connection(1002)
#     logger.log_tcp_connected(1003)
#     logger.log_preferred_neighbors([1002, 1004])
#     logger.log_optimistically_unchoked(1005)
#     logger.log_unchoked(1003)
#     logger.log_choked(1004)
#     logger.log_have(1005, 12)
#     logger.log_interested(1006)
#     logger.log_not_interested(1007)
#     logger.log_piece_downloaded(1002, 8, 10)
#     logger.log_complete_file_downloaded()

# if __name__ == "__main__":
#     test_logger()
#     print("Logger test complete. Check the logs/log_peer_1001.log file.")




