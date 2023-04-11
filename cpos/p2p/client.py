import logging
import socket

class Client:
    def __init__(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.peer_table = {} # map peer IDs to IP+ports
        self.connection_table = {} # map peer IDs to open socket connections

    def register(self, peer_id, peer_addr, peer_port):
        self.peer_table[peer_id] = (peer_addr, peer_port)

    def connect(self, peer_id):
        if peer_id not in self.peer_table:
            self.logger.error(f"Failed to connect to unknown peer: {peer_id}")
            return

        # TODO: handle connection errors
        addr, port = self.peer_table[peer_id]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.info(f"Attempting connection with peer {peer_id} ({addr}:{port})") 

        try:
            sock.connect((addr, port))
        except OSError as e:
            self.logger.error(f"Failed to connect to peer {peer_id}: {e}")
            return

        self.logger.error(f"Connected to peer {peer_id} ({addr}:{port})")
        if peer_id in self.connection_table:
            self.connection_table[peer_id].close()
        self.connection_table[peer_id] = sock

    def send(self, peer_id, msg):
        if peer_id not in self.peer_table:
            self.logger.error(f"Failed to send message to unknown peer: {peer_id}")
            return
        # TODO: we need to handle connection errors here
        if peer_id not in self.connection_table:
            self.logger.error(f"Not connected to peer {peer_id}")
            return

        sock = self.connection_table[peer_id]
        try:
            sock.sendall(msg)
        except OSError as e:
            self.logger.error(f"Failed to send message to peer {peer_id}: {e}")

        self.logger.debug(f"Sent message to peer {peer_id}: {msg}")
