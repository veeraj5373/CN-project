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

from config import Config
from file_manager import FileManager
import os

def test_file_manager():
    # Initialize the configuration class
    config = Config()

    # Get and print common configuration
    common_config = config.get_common_config()
    print("Common Configuration:")
    for key, value in common_config.items():
        print(f"{key}: {value}")

    # Get and print peer information
    peer_info = config.get_peer_config()
    print("\nPeer Information:")
    for peer in peer_info:
        print(f"Peer ID: {peer['peer_id']}, Host: {peer['host']}, Port: {peer['port']}, Has File: {peer['has_file']}")

    # Identify the peer that has the full file
    peer_id_with_file = None
    for peer in peer_info:
        if peer['has_file'] == 1:
            peer_id_with_file = peer['peer_id']
            break  # Stop once we find the peer with the file

    if peer_id_with_file:
        print(f"\nPeer with file (ID {peer_id_with_file}) found.")

        # Get the file name and other common configurations
        file_name = common_config['FileName']  # Just 'tree.jpg', file is in peer's folder
        file_size = common_config['FileSize']
        piece_size = common_config['PieceSize']

        # Construct the full file path based on peer ID (e.g., /path/to/peer_1001/tree.jpg)
        file_path = os.path.join(f"./{peer_id_with_file}", file_name)
        
        # Ensure the file exists at the constructed path
        if not os.path.exists(file_path):
            print(f"Error: The file {file_path} does not exist.")
            return

        # Initialize the FileManager for this peer
        file_manager = FileManager(file_path, file_size, piece_size, peer_id_with_file)

        # Now call the split_file_into_pieces method to test the functionality
        file_manager.split_file_into_pieces()

        # Optionally, you can reassemble the file to test the reassemble logic as well
        output_file_name = f"reassembled_{file_name.split('/')[-1]}"
        file_manager.reassemble_file(output_file_name)

    else:
        print("No peer with the full file found.")

if __name__ == "__main__":
    test_file_manager()





