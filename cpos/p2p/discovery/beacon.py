import logging
import socket
from typing import cast

from cpos.p2p.peer import Peer
from cpos.p2p.discovery.messages import Message, MessageCode, Hello, PeerList

class Beacon:
    def __init__(self, port: int):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.port = port 

        self.logger.info(f"Opening socket on port {self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind socket to all net interfaces (less than ideal)
        self.socket.bind(('', self.port))
        self.logger.info(f"Listening on port {self.port}")

        self.peers: list[Peer] = []

    def start(self):
        self.listen()

    def listen(self):
        while True:
            msg = addr = port = None

            try:
                recv, (addr, port) = self.socket.recvfrom(65536)
                msg = Message.deserialize(recv)
                self.logger.debug(f"received {len(recv)} bytes: {recv}")
            except Exception as e:
                self.logger.error(f"failed to deserialize message from {addr}:{port}, reason: {e}")
                continue


            
            self.logger.debug(f"handling message: {msg}")
            if isinstance(msg, Hello):
                peer = Peer(addr, msg.port, msg.id)
                if peer not in self.peers:
                    self.peers.append(peer)
                    self.logger.info(f"registering new peer ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port})")

            reply = PeerList(self.peers)
            self.logger.info(f"sending peerlist to ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port}): {self.peers}")
            try:
                sent = self.socket.sendto(reply.serialize(), (addr, port))
                self.logger.debug(f"sent {sent} bytes to ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port}): {self.peers}")
            except Exception as e:
                self.logger.error(f"unable to send reply to {peer}: {e}")



def main():
    b = Beacon(port=8888)

if __name__ == "__main__":
    main()
