import socket
import threading
import random
import time
import os
import struct
import pickle
from file_manager import FileManager
from config import Config
from logger import Logger
from message import Message

class Peer:
    def __init__(self, peer_id, config_files=('Common.cfg', 'PeerInfo.cfg')):
        self.peer_id = peer_id
        self.config = Config(*config_files)
        common_config = self.config.get_common_config()
        peer_info = self.config.get_peer_info(peer_id)

        if not peer_info:
            print(f"Error: Peer ID {peer_id} not found in PeerInfo.cfg")
            exit()

        self.host = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.host)
        self.port = peer_info['port']
        self.file_name = common_config.get('FileName')
        self.file_size = int(common_config.get('FileSize'))
        self.piece_size = int(common_config.get('PieceSize'))
        self.total_pieces = (self.file_size + self.piece_size - 1) // self.piece_size
        self.max_neighbors = int(common_config.get('NumberOfPreferredNeighbors', 1))
        self.unchoking_interval = int(common_config.get('UnchokingInterval'))
        self.optimistic_unchoking_interval = int(common_config.get('OptimisticUnchokingInterval'))

        self.storage_dir = str(self.peer_id)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.file_manager = FileManager(self.file_name, self.file_size, self.piece_size, self.peer_id)
        self.logger = Logger(self.peer_id)

        self.peers = {}
        self.connections = {}
        self.pieces = set()
        self.requested_pieces = set()
        self.piece_owners = {}
        self.download_rates = {}
        self.lock = threading.Lock()

        self.interested_peers = set()
        self.choked_peers = set()
        self.preferred_neighbors = set()
        self.optimistically_unchoked_neighbor = None
        self.active_neighbors = set()
        self.last_request_time = time.time()

        # Initialize completion tracking
        self.completion_file_path = os.path.join(self.storage_dir, 'completion.txt')
        open(self.completion_file_path, 'w').close()

        if self.config.has_complete_file(self.peer_id):
            self.pieces = set(range(self.total_pieces))
            self.file_manager.split_file_into_pieces()

        for pid, info in self.config.peer_info.items():
            if pid != self.peer_id:
                self.peers[pid] = (info['hostname'], info['port'])

        threading.Thread(target=self._start_server, daemon=True).start()
        threading.Thread(target=self._connect_to_initial_peers, daemon=True).start()
        threading.Thread(target=self._download_manager, daemon=True).start()
        threading.Thread(target=self._periodic_unchoke, daemon=True).start()
        threading.Thread(target=self._periodic_optimistic_unchoke, daemon=True).start()

    def _start_server(self):
        """Start the server socket to listen for incoming connections."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            self.logger.log(f"[Server] Listening on {self.host}:{self.port}...")

            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    if len(self.connections) < self.max_neighbors:
                        self.logger.log(f"[Server] Accepted connection from {addr}")
                        threading.Thread(
                            target=self._perform_handshake, 
                            args=(client_socket, False), 
                            daemon=True
                        ).start()
                    else:
                        self.logger.log("[Server] Rejected connection: max neighbors reached")
                        client_socket.close()
                except Exception as e:
                    self.logger.log(f"[Server] Error accepting connection: {e}")

        except Exception as e:
            self.logger.log(f"[Server] Failed to start server: {e}")


    def _connect_to_initial_peers(self):
        """Attempt to connect to initial peers in randomized order."""
        time.sleep(5)  # Wait for other peers to start their servers

        initial_peers_list = list(self.peers.items())
        random.shuffle(initial_peers_list)

        for peer_id, (host, port) in initial_peers_list:
            if peer_id <= self.peer_id:
                continue  # Avoid duplicate connections (only connect to higher peer IDs)
            if len(self.connections) >= self.max_neighbors:
                break  # Respect max neighbors limit
            if peer_id in self.connections:
                continue  # Already connected

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # Prevent hanging on connect
                sock.connect((host, port))
                self._perform_handshake(sock, is_initiator=True)
                self.logger.log(f"[Connection] Peer {self.peer_id} connected to Peer {peer_id} at {host}:{port} via TCP")
            except (socket.timeout, ConnectionRefusedError) as conn_err:
                self.logger.log(f"[Connection] Connection to Peer {peer_id} at {host}:{port} failed: {conn_err} via TCP")
            except Exception as e:
                self.logger.log(f"[Connection] Unexpected error connecting to Peer {peer_id} at {host}:{port}: {e} via TCP")


    def _perform_handshake(self, sock, is_initiator):
        """Perform the handshake protocol with another peer."""
        header = b'P2PFILESHARINGPROJ'
        zeros = b'\x00' * 10
        pid_bytes = struct.pack('>I', self.peer_id)
        handshake_msg = header + zeros + pid_bytes

        try:
            if is_initiator:
                sock.sendall(handshake_msg)
                data = sock.recv(32)
            else:
                data = sock.recv(32)
                sock.sendall(handshake_msg)

            if len(data) != 32 or data[:18] != header:
                self.logger.log("[Handshake] Invalid handshake received.")
                sock.close()
                return

            remote_peer_id = struct.unpack('>I', data[-4:])[0]

            if remote_peer_id == self.peer_id:
                self.logger.log(f"[Handshake] Ignored self-connection from Peer {remote_peer_id}")
                sock.close()
                return

            if remote_peer_id in self.connections:
                self.logger.log(f"[Handshake] Already connected to Peer {remote_peer_id}")
                sock.close()
                return

            if len(self.connections) >= self.max_neighbors:
                self.logger.log(f"[Handshake] Rejected Peer {remote_peer_id}: max neighbors reached")
                sock.close()
                return

            # Add the new peer to the connection list
            self.connections[remote_peer_id] = sock
            self.download_rates[remote_peer_id] = 0
            self.active_neighbors.add(remote_peer_id)
            self.logger.log_connection(remote_peer_id)

            # Start message receiving thread
            threading.Thread(
                target=self._receive_messages,
                args=(sock, remote_peer_id),
                daemon=True
            ).start()

            # Send bitfield message to the new peer
            self._send_bitfield(sock)

        except Exception as e:
            self.logger.log(f"[Handshake] Handshake with peer failed: {e}")
            sock.close()


    def _send_bitfield(self, sock):
        """Send the bitfield message indicating which pieces this peer has."""
        try:
            # Construct bitfield: 1 bit per piece, packed into bytes
            bitfield = bytearray((self.total_pieces + 7) // 8)
            for piece in self.pieces:
                byte_index = piece // 8
                bit_index = 7 - (piece % 8)
                bitfield[byte_index] |= (1 << bit_index)

            message = Message.bitfield(bitfield)
            sock.sendall(message)
            self.logger.log("[Bitfield] Sent bitfield message.")
        except Exception as e:
            self.logger.log(f"[Bitfield] Error sending bitfield: {e}")


    def _receive_messages(self, sock, peer_id):
        """Continuously receive and handle messages from a connected peer."""
        try:
            while True:
                # Read message length header
                header = sock.recv(4)
                if not header:
                    break

                length = struct.unpack('>I', header)[0]
                body = b''

                # Read the complete message body
                while len(body) < length:
                    chunk = sock.recv(length - len(body))
                    if not chunk:
                        break
                    body += chunk

                if len(body) != length:
                    self.logger.log(f"[Receive] Incomplete message from {peer_id}, expected {length} bytes.")
                    break

                msg_id, payload = Message.parse_message(header + body)

                if msg_id == Message.BITFIELD:
                    for i in range(self.total_pieces):
                        byte_index = i // 8
                        bit_index = 7 - (i % 8)
                        if byte_index < len(payload) and (payload[byte_index] & (1 << bit_index)):
                            self.piece_owners.setdefault(i, set()).add(peer_id)
                    self._send_request_for_piece(peer_id)

                elif msg_id == Message.HAVE:
                    piece_index = struct.unpack('>I', payload)[0]
                    self.piece_owners.setdefault(piece_index, set()).add(peer_id)
                    self._send_request_for_piece(peer_id)

                elif msg_id == Message.REQUEST:
                    self.last_request_time = time.time()
                    piece_index = struct.unpack('>I', payload)[0]
                    if piece_index in self.pieces:
                        data = self.file_manager.retrieve_piece(piece_index)
                        if data:
                            try:
                                sock.sendall(Message.piece(piece_index, data))
                                self.logger.log_sent_piece(peer_id, piece_index)
                            except Exception as e:
                                self.logger.log(f"[Send] Failed to send piece {piece_index} to {peer_id}: {e}")

                elif msg_id == Message.PIECE:
                    piece_index = struct.unpack('>I', payload[:4])[0]
                    data = payload[4:]
                    if piece_index not in self.pieces:
                        success = self.file_manager.save_piece(piece_index, data)
                        if success:
                            self.pieces.add(piece_index)
                            self.download_rates[peer_id] += len(data)
                            self.logger.log_received_piece(peer_id, piece_index, len(self.pieces))

                            self._check_download_completion()

                            # Notify all peers we now have this piece
                            for pid, conn in self.connections.items():
                                try:
                                    conn.sendall(Message.have(piece_index))
                                except Exception:
                                    self.logger.log(f"[Notify] Failed to notify {pid} about piece {piece_index}")
                            self._send_request_for_piece(peer_id)
        except Exception as e:
            self.logger.log(f"[Receive] Error receiving message from {peer_id}: {e}")
        finally:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            sock.close()
            self.connections.pop(peer_id, None)
            self.active_neighbors.discard(peer_id)

            self._connect_to_initial_peers()
            self.logger.log(f"[Connection] Closed connection to Peer {peer_id}")



    def _send_request_for_piece(self, peer_id):
        """Send a request for a needed piece to the specified peer."""
        if peer_id in self.choked_peers:
            self.logger.log(f"[Request] Peer {peer_id} is choked. No request sent.")
            return

        sock = self.connections.get(peer_id)
        if not sock:
            self.logger.log(f"[Request] No active connection to Peer {peer_id}")
            return

        available_pieces = [
            i for i in range(self.total_pieces) if peer_id in self.piece_owners.get(i, set())]

        needed_pieces = [
            piece for piece in available_pieces 
            if piece not in self.pieces and piece not in self.requested_pieces
        ]

        if not needed_pieces:
            self.logger.log(f"[Request] No needed pieces available from Peer {peer_id}")
            return

        # Choose a random piece to request
        random.shuffle(needed_pieces)
        piece_index = needed_pieces[0]
        self.requested_pieces.add(piece_index)

        try:
            sock.sendall(Message.request(piece_index))
            self.logger.log_requested_piece(peer_id, piece_index)
        except Exception as e:
            self.logger.log(f"[Request] Failed to request piece {piece_index} from Peer {peer_id}: {e}")
            self.connections.pop(peer_id, None)
            self.active_neighbors.discard(peer_id)
            self.choked_peers.discard(peer_id)



    def _update_interest(self, peer_id):
        """Update whether this peer is interested in pieces from the given peer."""
        # Check if the peer has any piece we need
        is_interesting = any(
            peer_id in self.piece_owners.get(i, set()) and i not in self.pieces
            for i in range(self.total_pieces)
        )

        if is_interesting:
            if peer_id not in self.interested_peers:
                self.logger.log(f"[Interest] Now interested in Peer {peer_id}")
            self.interested_peers.add(peer_id)
        else:
            if peer_id in self.interested_peers:
                self.logger.log(f"[Interest] No longer interested in Peer {peer_id}")
            self.interested_peers.discard(peer_id)


    def _periodic_unchoke(self):
            """Periodically unchoke preferred peers based on download rates."""
            while True:
                time.sleep(self.unchoking_interval)
                with self.lock:
                    sorted_peers = sorted(self.download_rates.items(), key=lambda x: x[1], reverse=True)
                    self.preferred_neighbors = set(pid for pid, _ in sorted_peers[:self.max_neighbors])

                    for peer_id in list(self.connections.keys()):
                        conn = self.connections[peer_id]
                        try:
                            if peer_id in self.preferred_neighbors:
                                if peer_id in self.choked_peers:
                                    conn.sendall(Message.unchoke())
                                    self.choked_peers.remove(peer_id)
                                    self.logger.log_unchoking(peer_id)
                                    self.logger.log(f"[Log] Peer {peer_id} was unchoked and added to preferred neighbors.")
                            elif peer_id != self.optimistically_unchoked_neighbor:
                                if peer_id not in self.choked_peers:
                                    conn.sendall(Message.choke())
                                    self.choked_peers.add(peer_id)
                                    self.logger.log_choking(peer_id)
                                    self.logger.log(f"[Log] Peer {peer_id} was choked and removed from preferred neighbors.")
                        except Exception as e:
                            self.logger.log(f"[Unchoke] Error with Peer {peer_id}: {e}")
                            conn.close()
                            self.connections.pop(peer_id, None)
                            self.choked_peers.discard(peer_id)
                            self.active_neighbors.discard(peer_id)

    def _periodic_optimistic_unchoke(self):
            while True:
                time.sleep(self.optimistic_unchoking_interval)
                with self.lock:
                    if self.optimistically_unchoked_neighbor:
                        peer_id = self.optimistically_unchoked_neighbor
                        if peer_id not in self.preferred_neighbors:
                            conn = self.connections.get(peer_id)
                            if conn:
                                try:
                                    conn.sendall(Message.choke())
                                    self.logger.log_choking(peer_id)
                                except Exception:
                                    pass
                            self.optimistically_unchoked_neighbor = None

                    candidates = list(self.interested_peers - self.preferred_neighbors)
                    random.shuffle(candidates)
                    for peer_id in candidates:
                        conn = self.connections.get(peer_id)
                        if not conn:
                            continue
                        try:
                            conn.sendall(Message.unchoke())
                            self.optimistically_unchoked_neighbor = peer_id
                            self.logger.log_unchoking(peer_id)
                            self.logger.log_change_optimistically_unchoked_neighbor(peer_id)
                            break
                        except Exception:
                            continue
    
    def choking_manager(self, interval=10):
        while True:
            time.sleep(interval)
            with self.lock:
                top_peers = self.select_top_peers_by_download_rate(top_n=2)
                new_choked = set(self.connections.keys()) - set(top_peers)
                new_unchoked = set(top_peers)

                # Choke peers not in top N
                for peer_id in new_choked:
                    if peer_id not in self.choked_peers:
                        self.send_choke(peer_id)
                        self.choked_peers.add(peer_id)

                # Unchoke top N peers
                for peer_id in new_unchoked:
                    if peer_id in self.choked_peers:
                        self.send_unchoke(peer_id)
                        self.choked_peers.remove(peer_id)



    def _wait_for_all_peers_completion(self):
        self.logger.log(f"[Wait] Waiting for all peers to complete...")

        while True:
            completed_peers = set()
            for pid in self.peers.keys() | {self.peer_id}:
                path = os.path.join(str(pid), 'completion.txt')
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        completed_peers.update(line.strip() for line in f if line.strip().isdigit())

            if len(completed_peers) >= len(self.peers) + 1:  # +1 for self
                self.logger.log(f"[Exit] All peers have completed. Shutting down.")
                for conn in list(self.connections.values()):
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                        conn.close()
                    except:
                        pass
                os._exit(0)

            time.sleep(5)
    
    def _check_download_completion(self):
        if len(self.pieces) == self.total_pieces:
            self.logger.log(f"[Complete] Peer {self.peer_id} has received all pieces.")

            # Write to completion.txt to indicate this peer is done
            with open(self.completion_file_path, 'a') as f:
                f.write(f"{self.peer_id}\n")

            self.logger.log(f"[Complete] Peer {self.peer_id} wrote completion status. Waiting for all peers...")

            # Wait until all peers have completed
            self._wait_for_all_peers_completion()





    def _handle_connection(self, sock, addr, is_initiator=False, remote_peer_id=None):
        """Handle an incoming connection from a peer using Message protocol handshake."""
        try:
            # Receive handshake
            handshake_data = sock.recv(32)
            if len(handshake_data) != 32 or handshake_data[:18] != b'P2PFILESHARINGPROJ':
                self.logger.log(f"[Handle] Invalid handshake from {addr}")
                sock.close()
                return

            remote_peer_id = struct.unpack('>I', handshake_data[-4:])[0]

            if remote_peer_id == self.peer_id or remote_peer_id in self.connections:
                self.logger.log(f"[Handle] Ignoring duplicate/self-connection from Peer {remote_peer_id}")
                sock.close()
                return

            if len(self.connections) >= self.max_neighbors:
                self.logger.log(f"[Handle] Rejecting Peer {remote_peer_id}: max neighbors reached")
                sock.close()
                return

            # Add connection
            self.connections[remote_peer_id] = sock
            self.active_neighbors.add(remote_peer_id)
            self.logger.log_connection(remote_peer_id)

            # Send handshake back
            header = b'P2PFILESHARINGPROJ' + b'\x00' * 10 + struct.pack('>I', self.peer_id)
            sock.sendall(header)

            # Start receiving messages
            threading.Thread(target=self._receive_messages, args=(sock, remote_peer_id), daemon=True).start()

            # Send initial HAVE messages
            self._send_initial_have_messages(sock)

        except Exception as e:
            self.logger.log(f"[Handle] Error handling connection from {addr}: {e}")
            sock.close()



    def _download_manager(self):
        """Continuously manage download requests for needed pieces from connected peers."""
        while True:
            if not self.connections:
                time.sleep(1)
                continue

            for peer_id in list(self.active_neighbors):
                if peer_id in self.choked_peers or peer_id not in self.connections:
                    continue

                needed_pieces = [
                    i for i in range(self.total_pieces)
                    if i not in self.pieces and peer_id in self.piece_owners.get(i, set())
                ]

                if not needed_pieces:
                    continue

                random.shuffle(needed_pieces)
                piece_index = needed_pieces[0]

                if piece_index in self.requested_pieces:
                    continue

                self.requested_pieces.add(piece_index)

                try:
                    self.connections[peer_id].sendall(Message.request(piece_index))
                    self.logger.log_requested_piece(peer_id, piece_index)

                except Exception as e:
                    self.logger.log(f"[Download] Failed to request piece {piece_index} from Peer {peer_id}: {e}")
                    try:
                        self.connections[peer_id].shutdown(socket.SHUT_RDWR)
                        self.connections[peer_id].close()
                    except:
                        pass
                    self.connections.pop(peer_id, None)
                    self.active_neighbors.discard(peer_id)
                    self.choked_peers.discard(peer_id)

            time.sleep(1)


