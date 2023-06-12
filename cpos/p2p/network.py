from typing import Optional
import zmq
import logging

class Network:
    def __init__(self, id: bytes, port: int | str):
        self.port = port
        self.id = id

        logger = logging.getLogger(__name__ + id.hex())
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: [{self.id.hex()[0:8]}] %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.setsockopt(zmq.IDENTITY, self.id)

        # this makes us able to use a Poller to async-ly read
        # the socket if data is available, as well as know when a
        # peer is unreachable
        self.socket.setsockopt(zmq.ROUTER_MANDATORY, 1)

        self.socket.bind(f"tcp://*:{self.port}")

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.logger.info(f"listening on port {self.port}")

        self.known_peers: list[bytes] = []

    def connect(self, peer_ip: str, peer_port: int | str, peer_id: Optional[bytes]=None):
        self.logger.info(f"connecting to peer {peer_id.hex() if peer_id is not None else '[undefined]'} at tcp://{peer_ip}:{peer_port}")
        self.socket.connect(f"tcp://{peer_ip}:{peer_port}")
        if peer_id is not None:
            self.known_peers.append(peer_id)

    # https://github.com/zeromq/pyzmq/issues/1646
    def send(self, peer_id: bytes, msg: bytes):
        if peer_id in self.known_peers:
            try:
                self.logger.debug(f"sending message to peer {peer_id.hex()[0:8]}: {msg}")
                self.socket.send_multipart([peer_id, bytes(), msg], zmq.NOBLOCK)
            except Exception as e:
                self.logger.error(f"failed to send message to peer {peer_id.hex()[0:8]} ({e})")
                
        else:
            self.logger.error(f"failed to send message to unknown peer: {peer_id.hex()}")

    def read(self, timeout=0) -> Optional[bytes]:
        # self.logger.debug(f"trying to read socket (timeout={timeout})")
        # read from poller with a timeout (if it's 0, returns immediately)
        if not self.poller.poll(timeout):
            return None
        peer_id, _, msg = self.socket.recv_multipart()
        self.logger.debug(f"received message from peer {peer_id.hex()[0:8]}: {msg}")
        if peer_id not in self.known_peers:
            self.known_peers.append(peer_id)
        return msg
