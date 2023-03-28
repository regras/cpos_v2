import logging
import socket

class PeerConnection:
    def __init__(self, peer_addr, peer_port):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.peer_addr = peer_addr
        self.peer_port = peer_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((peer_addr, peer_port))
        logger.debug(f"Connected to peer at {peer_addr}:{peer_port}; sending heartbeat")
        self.socket.sendall(b"Hello peer")
