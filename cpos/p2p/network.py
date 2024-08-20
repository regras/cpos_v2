from typing import Optional
import zmq
import logging

from cpos.p2p.discovery.client import Client as DiscoveryClient

class Network:
    def __init__(self, id: bytes, port: int | str, beacon_ip: str, beacon_port: int | str):
        self.port = port
        self.id = id

        logger = logging.getLogger(__name__ + id.hex())
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: [{self.id.hex()[0:8]}] %(message)s")
        logger.setLevel(logging.WARNING)
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

        self.beacon_ip = beacon_ip
        self.beacon_port = beacon_port
        self.known_peers: list[bytes] = []
        self.peer_failed_msg_count = {}
        if self.beacon_ip is None or self.beacon_port is None:
            self.logger.error(f"missing beacon network info!")
            return
        
        self.client = DiscoveryClient(self.beacon_ip, self.beacon_port, self.port, self.id)

    def connect(self, peer_ip: str, peer_port: int | str, peer_id: Optional[bytes]=None):
        self.logger.info(f"connecting to peer {peer_id.hex() if peer_id is not None else '[undefined]'} at tcp://{peer_ip}:{peer_port}")
        self.socket.connect(f"tcp://{peer_ip}:{peer_port}")
        if peer_id is not None:
            self.known_peers.append(peer_id)
            self.peer_failed_msg_count[peer_id] = 0

    # https://github.com/zeromq/pyzmq/issues/1646
    def send(self, peer_id: bytes, msg: bytes):
        if peer_id in self.known_peers:
            try:
                self.logger.debug(f"sending message to peer {peer_id.hex()[0:8]}")
                self.socket.send_multipart([peer_id, bytes(), msg], zmq.NOBLOCK)
                self.peer_failed_msg_count[peer_id] = 0
                return True
            except Exception as e:
                self.peer_failed_msg_count[peer_id] += 1 
                self.logger.error(f"failed to send message to peer {peer_id.hex()[0:8]}, failure number: {self.peer_failed_msg_count[peer_id]}, ({e})")
                self.logger.error(f"known_peers: {self.known_peers}")
                if self.peer_failed_msg_count[peer_id] >= 3:
                    self.forget_peer(peer_id)
                return False
        else:
            self.logger.error(f"failed to send message to unknown peer: {peer_id.hex()}")
            return False

    def read(self, timeout=0) -> Optional[bytes]:
        # self.logger.debug(f"trying to read socket (timeout={timeout})")
        # read from poller with a timeout (if it's 0, returns immediately)
        if not self.poller.poll(timeout):
            return None
        peer_id, _, msg = self.socket.recv_multipart()
        self.logger.debug(f"received message from peer {peer_id.hex()[0:8]}: {msg}")
        if peer_id not in self.known_peers:
            self.known_peers.append(peer_id)
            self.logger.debug(f"New peer added by receiving a message: {peer_id.hex()[0:8]}")
            self.peer_failed_msg_count[peer_id] = 0
        return msg
    
    def forget_peer(self, peer_id: bytes):
        self.logger.info(f"Forgetting peer: {peer_id.hex()[0:8]}")
        try:
            self.known_peers.remove(peer_id)
            del self.peer_failed_msg_count[peer_id]
        except Exception as e:
            self.logger.error(f"Couldnt find peer to delete: {peer_id.hex()[0:8]}")

        # TODO CLOSE TCP CONNECTION 
        # I couldnt find an easy way to do that. Maybe zmq's garbage collector closes the TCP connection eventually, but I am not sure


    def get_peerlist_from_beacon(self):
        peerlist = self.client.get_peerlist()
        if peerlist is not None:
            return peerlist

    def get_additional_peers_from_beacon(self):
        # Gets same nuber of peers from beacon as initial contact
        peerlist = self.client.get_additional_peers()
        if peerlist is not None:
            return peerlist
    
    def notify_beacon(self):
        # Notifies beacon this node is still alive and connected to the network
        self.client.notify_beacon()


