from __future__ import annotations
import json
from base64 import b64encode, b64decode

from cpos.core.block import Block
from cpos.core.transactions import TransactionList

class MessageCode:
    UNDEFINED = 0x0
    HELLO = 0x1
    BLOCK_BROADCAST = 0x2

class MessageParseError(Exception):
    pass

class Message:
    """Class that represents the protocol message frames."""

    def __init__(self):
        self.code = 0x0
        pass

    def serialize(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def deserialize(cls, raw) -> Message:
        raise NotImplementedError


class Hello(Message):
    def __init__(self, peer_id: bytes, peer_port: int | str):
        self.msg_code = MessageCode.HELLO
        self.peer_id = peer_id
        self.peer_port = peer_port

    def serialize(self) -> bytes:
        data = {}
        data["peer_id"] = b64encode(self.peer_id).decode("ascii")
        data["peer_port"] = self.peer_port
        return bytes(json.dumps(data), "ascii")

    @classmethod
    def deserialize(cls, raw: bytes) -> Hello:
        raw_dict = json.loads(raw.decode("ascii"))
        peer_id = b64decode(raw_dict["peer_id"])
        peer_port = raw_dict["peer_port"]
        msg = Hello(peer_id, peer_port)
        return msg

    def __str__(self):
        return f"Hello(id={self.peer_id}, port={self.peer_port})"

class BlockBroadcast(Message):
    def __init__(self, block: Block):
        self.code = MessageCode.BLOCK_BROADCAST
        self.block = block

    def serialize(self) -> bytes:
        # TODO: this is horribly ugly, we need to find a decent serialization strategy
        fields = ["hash", "parent_hash", "transaction_hash", "owner_pubkey", "signed_node_hash", "index", "round", "ticket_number"]
        b = self.block
        data = {}
        for field in fields:
            entry = b.__dict__[field]
            if isinstance(entry, bytes):
                data[field] = b64encode(entry).decode("ascii")
            else:
                data[field] = entry
        return bytes(json.dumps(data), 'ascii')
    
    @classmethod
    def deserialize(cls, raw: bytes) -> BlockBroadcast:
        fields = ["hash", "parent_hash", "transaction_hash", "owner_pubkey", "index", "round", "ticket_number"]
        raw_dict = json.loads(raw.decode("ascii"))
        print(f"deserialized: {raw_dict}")
        # TODO: this transaction stub needs to be implemented eventually
        stub = TransactionList()
        parent_hash = b64decode(raw_dict["parent_hash"])
        owner_pubkey = b64decode(raw_dict["owner_pubkey"])
        signed_node_hash = b64decode(raw_dict["signed_node_hash"])
        block = Block(parent_hash = parent_hash,
                      transactions = stub,
                      owner_pubkey = owner_pubkey,
                      signed_node_hash = signed_node_hash,
                      round = raw_dict["round"],
                      index = raw_dict["index"],
                      ticket_number = raw_dict["ticket_number"])
        return BlockBroadcast(block)
        # except Exception as e:
        #     print(e)
        #     raise ValueError("invalid block serialization")
