from __future__ import annotations
import json

class MessageCode:
    UNDEFINED = 0x0
    HELLO = 0x1

class MessageParseError(Exception):
    pass

class Message:
    """Class that represents the protocol message frames."""

    def __init__(self):
        self.code = 0x0
        pass

    def serialize(self) -> bytes:
        return str.encode(json.dumps(self.__dict__))

    @classmethod
    def deserialize(cls, raw_msg) -> Message:
        # We import annotations here in order to make the return type
        # in the signature available within the class definition
        return json.loads(raw_msg)


class Hello(Message):
    def __init__(self, peer_id, peer_port):
        self.msg_code = MessageCode.HELLO
        self.peer_id = peer_id
        self.peer_port = peer_port
