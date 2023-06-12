from __future__ import annotations

class Peer:
    def __init__(self, peer_ip: str, peer_port: int, peer_id: bytes):
        self.ip = peer_ip
        self.port= peer_port
        self.id = peer_id
    
    def __str__(self):
        return f"({self.ip}:{self.port}, {self.id.hex()[0:8]})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, peer: Peer):
        return self.id == peer.id
