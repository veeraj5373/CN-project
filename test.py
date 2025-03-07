# this is used for testing the code

from config import Config

def run_config_test():
    # Initialize the configuration class (paths are already set in the config file)
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
    
    
    peer_id = 1001 
    specific_peer_info = config.get_peer_info(peer_id)
    if specific_peer_info:
        print(f"\nSpecific Peer (ID {peer_id}) Information:")
        for key, value in specific_peer_info.items():
            print(f"{key}: {value}")
    else:
        print(f"\nPeer with ID {peer_id} not found.")

if __name__ == "__main__":
    run_config_test()
