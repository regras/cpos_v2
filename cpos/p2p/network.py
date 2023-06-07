import zmq
import logging

class Network:
    def __init__(self, id: bytes, port: int | str = 8888):
        self.port = port
        self.id = id

        logger = logging.getLogger(__name__ + id.hex())
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: [0x{self.id.hex()[0:8]}] %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.id)
        # self.socket.setsockopt(zmq.ROUTER_MANDATORY, 1)
        self.socket.bind(f"tcp://*:{self.port}")

        self.logger.info(f"listening on port {self.port}")

        self.known_peers = []

    def connect(self, peer_id: bytes, peer_ip: str, peer_port: int | str):
        self.socket.connect(f"tcp://{peer_ip}:{peer_port}")
        self.known_peers.append(peer_id)

    # https://github.com/zeromq/pyzmq/issues/1646
    def send(self, peer_id: bytes, msg: bytes):
        if peer_id in self.known_peers:
            self.socket.send_multipart([peer_id, bytes(), msg])
            self.logger.debug(f"sending message to peer 0x{peer_id.hex()}: {msg}")
        else:
            self.logger.error(f"failed to send message to unknown peer: {peer_id.hex()}")

    def read(self) -> bytes:
        peer_id, _, msg = self.socket.recv_multipart()
        self.logger.debug(f"received message from peer {peer_id.hex()[0:8]}: {msg}")
        if peer_id not in self.known_peers:
            self.known_peers.append(peer_id)
        return msg
