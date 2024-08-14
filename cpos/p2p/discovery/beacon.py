import logging
import random
import socket
import threading
from typing import cast
from threading import Thread, Semaphore
from time import time
import os

from cpos.p2p.peer import Peer
from cpos.p2p.discovery.messages import Message, MessageCode, Hello, PeerList, PeerListRequest, NotifyBeacon

class Beacon:
    def __init__(self, port: int, instant_reply: bool = True):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.port = port 

        self.logger.info(f"Opening socket on port {self.port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # bind socket to all net interfaces (less than ideal)
        self.socket.bind(('', self.port))

        self.peers: list[Peer] = []
        self.peers_still_alive_flags = {}

        self.current_round = 0
        self.initial_timestamp = time() # This doesnt need to be sincronized with the nodes, it only needs to have the same round time
        self.num_peers_send = int(os.environ.get("NUM_PEERS_SEND", "5"))
        self.round_time = int(os.environ.get("ROUND_TIME", "20"))

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
        self.socket.settimeout(1)

        self.semaphore.acquire()
        while True:
            if self.should_halt:
                self.logger.debug(f"received halting signal")
                self.semaphore.release()
                return

            msg = addr = port = None

            self.update_round()

            try:
                recv, (addr, port) = self.socket.recvfrom(65536)
                msg = Message.deserialize(recv)
                self.logger.debug(f"received {len(recv)} bytes: {recv}")
            except socket.timeout as e:
                # self.logger.debug("read timeout")
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
                    self.peers_still_alive_flags[peer.id] = 1
                    self.logger.info(f"registering new peer ({peer.id.hex()[0:8]}, {peer.ip}:{peer.port})")
            

            if (isinstance(msg, Hello) or isinstance(msg, PeerListRequest)):
                count = min(self.num_peers_send, len(self.peers))
                random_peers = random.sample(self.peers, count)
                reply = PeerList(random_peers)
                try:
                    sent = self.socket.sendto(reply.serialize(), (addr, port))
                    self.logger.debug(f"sent {sent} bytes to ({addr}, {port}): {random_peers}")
                except Exception as e:
                    self.logger.error(f"unable to send reply to ({addr}, {port}): {e}")
            else:
                self.reply_queue.append((addr, port))

            if isinstance(msg, NotifyBeacon):
                addr = msg.ip
                peer = Peer(addr, msg.port, msg.id)
                self.peers_still_alive_flags[msg.id] = 1
                if not peer in self.peers:
                    self.peers.append(peer)
    

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

    def manage_peer_forgetting(self):
        # O(n), using list.remove() would be O(n^2)
        new_peerlist = []
        for peer in self.peers:
            if self.peers_still_alive_flags[peer.id] == 0:
                del self.peers_still_alive_flags[peer.id]
                self.logger.info(f"Forgetting inactive peer {peer.id.hex()[0:8]}")
            else:
                self.peers_still_alive_flags[peer.id] = 0
                new_peerlist.append(peer)
        self.peers = new_peerlist
        self.logger.debug(f"Current known peers: {self.peers}")

    def update_round(self):
        current_time = time()
        delta_t = current_time - self.initial_timestamp
        round = int(delta_t / self.round_time)

        if self.current_round == round:
            return

        self.current_round = round
        self.logger.info(f"Beacon starting new round: {self.current_round}")

        if self.current_round % 3 == 0:
            self.manage_peer_forgetting()




def main():
    b = Beacon(port=8888)

if __name__ == "__main__":
    main()
