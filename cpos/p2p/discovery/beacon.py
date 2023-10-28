import logging
import random
import socket
import threading
from typing import cast
from threading import Thread, Semaphore

from cpos.p2p.peer import Peer
from cpos.p2p.discovery.messages import Message, MessageCode, Hello, PeerList

class Beacon:
    def __init__(self, port: int, instant_reply: bool = True):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.port = port 

        self.logger.info(f"Opening socket on port {self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind socket to all net interfaces (less than ideal)
        self.socket.bind(('', self.port))

        self.peers: list[Peer] = []
        self.instant_reply = instant_reply
        self.should_halt = False
        self.reply_queue = []

        self.listener_thread = None
        self.semaphore = Semaphore()

    def start(self):
        if self.instant_reply:
            self.listen()
        else:
            self.listener_thread = Thread(target=self.listen)
            self.listener_thread.start()

    def halt(self):
        self.should_halt = True
        # wait for the listener thread to stop
        self.logger.warning("halting listener thread...")
        self.semaphore.acquire()
        self.should_halt = False
        self.semaphore.release()
        self.logger.warning("halted!")

    def listen(self):
        self.logger.info(f"Listening on port {self.port}")
        if not self.instant_reply:
            self.socket.settimeout(1)

        self.semaphore.acquire()
        while True:
            if self.should_halt:
                self.logger.debug(f"received halting signal")
                self.semaphore.release()
                return

            msg = addr = port = None

            try:
                recv, (addr, port) = self.socket.recvfrom(65536)
                msg = Message.deserialize(recv)
                self.logger.debug(f"received {len(recv)} bytes: {recv}")
            except socket.timeout as e:
                self.logger.debug("read timeout")
                continue
            except Exception as e:
                self.logger.error(f"failed to deserialize message from {addr}:{port}, reason: {e}")
                continue

            self.logger.debug(f"handling message: {msg}")
            if isinstance(msg, Hello):
                addr = msg.ip
                peer = Peer(addr, msg.port, msg.id)
                if peer not in self.peers:
                    self.peers.append(peer)
                    self.logger.info(f"registering new peer ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port})")

            if self.instant_reply:
                reply = PeerList(self.peers)
                self.logger.info(f"sending peerlist to ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port}): {self.peers}")
                try:
                    sent = self.socket.sendto(reply.serialize(), (addr, port))
                    self.logger.debug(f"sent {sent} bytes to ({addr}, {port}): {self.peers}")
                except Exception as e:
                    self.logger.error(f"unable to send reply to {peer}: {e}")
            else:
                self.reply_queue.append((addr, port))
    

    # flush the reply queue, i.e., reply to all received requests
    # when we're not in instant reply mode
    def broadcast_peerlist(self):
        self.logger.info("replying to peerlist requests")
        self.logger.debug(f"known peers: {self.peers}")
        for (addr, port) in self.reply_queue:
            msg = PeerList(self.peers)
            self.logger.info(f"sending peerlist to ({addr}, {port}): {self.peers}")
            try:
                sent = self.socket.sendto(msg.serialize(), (addr, port))
                self.logger.debug(f"sent {sent} bytes to ({addr}, {port}): {self.peers}")
            except Exception as e:
                self.logger.error(f"unable to send reply to ({addr}, {port}): {e}")

    def broadcast_random_peers(self, count: int = 5):
        self.logger.info("replying to peerlist requests")
        self.logger.debug(f"known peers: {self.peers}")
        count = min(count, len(self.peers))
        for (addr, port) in self.reply_queue:
            random_peers = random.sample(self.peers, count)
            msg = PeerList(random_peers)
            self.logger.info(f"sending peerlist to ({addr}, {port}): {self.peers}")
            try:
                sent = self.socket.sendto(msg.serialize(), (addr, port))
                self.logger.debug(f"sent {sent} bytes to ({addr}, {port}): {self.peers}")
            except Exception as e:
                self.logger.error(f"unable to send reply to ({addr}, {port}): {e}")



def main():
    b = Beacon(port=8888)

if __name__ == "__main__":
    main()
