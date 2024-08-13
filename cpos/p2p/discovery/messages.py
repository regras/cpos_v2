from typing import Self
import pickle
from cpos.p2p.peer import Peer

class MessageCode:
    UNIMPLEMENTED = 0xFF,
    HELLO = 0x0,
    PEERLIST = 0x1,
    PEER_LIST_REQUEST = 0x2,
    NOTIFY_BEACON = 0x3,

class Message:
    def __init__(self, code):
        self.code = MessageCode.UNIMPLEMENTED

    def serialize(self) -> bytes:
        msg_raw = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        return msg_raw

    @classmethod
    def deserialize(cls, raw) -> Self:
        return pickle.loads(raw)

class Hello(Message):
    def __init__(self, port: int, id: bytes, ip: str):
        self.code = MessageCode.HELLO
        self.port = port
        self.id = id
        self.ip = ip
    
    def __str__(self):
        return f"SelfIntroduction: (port={self.port}, id={self.id.hex()[0:8]}, ip={self.ip})"

class PeerList(Message):
    def __init__(self, peerlist: list[Peer]):
        self.code = MessageCode.PEERLIST
        self.peers = peerlist

    def __str__(self):
        return f"{self.peers}"
    
    def __repr__(self):
        return self.__str__()

class PeerListRequest(Message):
    def __init__(self, requester_id: bytes):
        self.code = MessageCode.PEER_LIST_REQUEST
        self.requester_id = requester_id

class NotifyBeacon(Message):
    def __init__(self, port: int, id: bytes, ip: str):
        self.code = MessageCode.NOTIFY_BEACON
        self.port = port
        self.id = id
        self.ip = ip
