from __future__ import annotations
import json


class MessageId:
    def __init__(self):
        pass

    HELLO = 0x1


class MessageParseError(Exception):
    pass


class Message:
    """Class that represents the protocol message frames."""

    def __init__(self):
        pass

    def serialize(self) -> str:
        raise NotImplementedError("Serialization unsupported")

    @classmethod
    def deserialize(cls, bytes) -> Message:
        # We import annotations here in order to make the return type
        # in the signature available within the class definition
        raise NotImplementedError("Deserialization unsupported")


class Hello(Message):
    def __init__(self):
        self.msg_id = MessageId.HELLO 

    def serialize(self) -> str:
        return json.dumps(self.__dict__)
