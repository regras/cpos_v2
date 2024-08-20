from time import sleep
from typing import Optional
from cpos.p2p.peer import Peer
from cpos.p2p.discovery.messages import Message, Hello, PeerList, PeerListRequest, NotifyBeacon

import fcntl
import socket
import struct
import logging
from threading import Thread

class Client:
    def __init__(self, beacon_ip: str, beacon_port: int, port: int, id: bytes):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self.beacon_ip = beacon_ip
        self.beacon_port = beacon_port

        self.port = port
        self.id = id
        self.ip = self._get_ip_address("eth0")

    def _get_ip_address(self, interface: str) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        packed_iface = struct.pack('256s', interface.encode('utf_8'))
        packed_addr = fcntl.ioctl(sock.fileno(), 0x8915, packed_iface)[20:24]
        return socket.inet_ntoa(packed_addr)

    def get_peerlist(self) -> Optional[list[Peer]]:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.logger.info(f"introducing self to beacon at {self.beacon_ip}:{self.beacon_port}")

        msg = Hello(self.port, self.id, self.ip)

        try:
            self.socket.sendto(msg.serialize(), (self.beacon_ip, self.beacon_port))
        except Exception as e:
            self.logger.error(f"failed to contact beacon: {e}")
            return None

        wait = 2
        self.logger.debug(f"sleeping for {wait} seconds")
        sleep(wait)
        self.logger.debug(f"listening for beacon response...")

        response = None
        try:
            response = self.socket.recv(65535)
            self.logger.debug(f"got response from beacon: {response}")
        except Exception as e:
            self.logger.error(f"error reading beacon response: {e}")
            return None

        try:
            msg = Message.deserialize(response)
            self.logger.debug(f"response: {msg}")
        except Exception as e:
            self.logger.error(f"failed to deserialize beacon response: {e}")
            return None
        
        if isinstance(msg, PeerList):
            return msg.peers

    def get_additional_peers(self) -> Optional[list[Peer]]:

        msg = PeerListRequest(self.id)

        try:
            self.socket.sendto(msg.serialize(), (self.beacon_ip, self.beacon_port))
        except Exception as e:
            self.logger.error(f"failed to contact beacon: {e}")
            return None

        wait = 2
        self.logger.debug(f"sleeping for {wait} seconds")
        sleep(wait)
        self.logger.debug(f"listening for beacon response...")

        response = None
        try:
            response = self.socket.recv(65535)
            self.logger.debug(f"got response from beacon: {response}")
        except Exception as e:
            self.logger.error(f"error reading beacon response: {e}")
            return None

        try:
            msg = Message.deserialize(response)
            self.logger.debug(f"response: {msg}")
        except Exception as e:
            self.logger.error(f"failed to deserialize beacon response: {e}")
            return None
        
        if isinstance(msg, PeerList):
            return msg.peers

    def notify_beacon(self) -> Optional[list[Peer]]:

        msg = NotifyBeacon(self.port, self.id, self.ip)

        try:
            self.socket.sendto(msg.serialize(), (self.beacon_ip, self.beacon_port))
        except Exception as e:
            self.logger.error(f"failed to contact beacon: {e}")
            return None


def main():
    beacon_ip = "localhost"
    beacon_port = 8888
    client_info: list[tuple[bytes, int]] = []
    initial_port = 9000
    total_clients = 20
    for i in range(total_clients):
        client_info.append((i.to_bytes(byteorder='little', signed=False), 9000))

    clients = []
    threads = []
    for (client_id, client_port) in client_info:
        def launch_client():
            new_client = Client(beacon_ip, beacon_port, client_port, client_id)
            new_client.get_peerlist()
        t = Thread(target=launch_client, args=())
        t.start()
        threads.append(t)
        # clients.append(new_client)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()

