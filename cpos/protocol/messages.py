from __future__ import annotations
import json
from base64 import b64encode, b64decode
import pickle
from typing import Self

from cpos.core.block import Block
from cpos.core.transactions import TransactionList

class MessageCode:
    UNDEFINED = 0x0
    HELLO = 0x1
    BLOCK_BROADCAST = 0x2
    PEER_LIST_REQUEST = 0x3
    PEER_LIST = 0x4

class MessageParseError(Exception):
    pass

class Message:
    """Class that represents the protocol message frames."""

    def __init__(self):
        self.code = 0x0
        pass

    def serialize(self) -> bytes:
        return pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def deserialize(cls, raw) -> Self:
        return pickle.loads(raw)


class Hello(Message):
    def __init__(self, peer_id: bytes, peer_port: int | str):
        self.code = MessageCode.HELLO
        self.peer_id = peer_id
        self.peer_port = peer_port

    def __str__(self):
        return f"Hello(id={self.peer_id.hex()[0:8]}, port={self.peer_port})"

class BlockBroadcast(Message):
    def __init__(self, block: Block, peer_id: bytes):
        self.code = MessageCode.BLOCK_BROADCAST
        self.block = block
        self.peer_id = peer_id

    def __str__(self):
        return self.block.__str__()
    
    def __repr__(self):
        return self.__str__()

class PeerListRequest(Message):
    def __init__(self, node_id: bytes):
        self.code = MessageCode.PEER_LIST_REQUEST
        self.node_id = node_id

class PeerList(Message):
    def __init__(self, peerlist: list[tuple[str, str | int, bytes]]):
        self.code = MessageCode.PEER_LIST
        self.peerlist = peerlist

# Ask for the last `block_count` blocks in peer's blockchain view
class ResyncRequest(Message):
    def __init__(self, peer_id: bytes, block_index: int):
        self.peer_id = peer_id
        self.block_index = block_index

    def __str__(self):
        return f"ResyncRequest(peer_id={self.peer_id})"

    def __repr__(self):
        return self.__str__()

class ResyncResponse(Message):
    def __init__(self, block_received: Block):
        self.block_received = block_received
