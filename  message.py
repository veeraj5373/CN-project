
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