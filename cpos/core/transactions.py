from __future__ import annotations

class TransactionList:
    def __init__(self):
        self.data = b""
        pass
    def serialize(self) -> bytes:
        pass
    @classmethod
    def deserialize(cls, raw: bytes) -> TransactionList:
        pass
    def get_hash(self) -> bytes:
        pass

# generating random bytes: https://bobbyhadz.com/blog/python-generate-random-bytes
# encoding binary data with base64: https://stackabuse.com/encoding-and-decoding-base64-strings-in-python/
# working with JSON in python: https://www.freecodecamp.org/portuguese/news/ler-arquivos-json-em-python-como-usar-load-loads-e-dump-dumps-com-arquivos-json/
# workflow: generate random bytes -> convert to base64 -> serialize to JSON
class MockTransactionList(TransactionList):
    def __init__(self):
        # insert random data
        pass
    def serialize(self) -> bytes:
        pass
    @classmethod
    def deserialize(cls, raw: bytes) -> TransactionList:
        pass
    def get_hash(self):
        pass
