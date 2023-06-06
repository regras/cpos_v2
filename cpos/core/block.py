from __future__ import annotations
from hashlib import sha256
from cpos.core.transactions import TransactionList
from time import time

class Block:
    # TODO: document the following changes:
    # - Use regular SHA-256 hashes instead of Merkle tree roots for transactions
    # - Use the node's pubkey as its ID
    # - When calculating the node hash, use the hash of the previous block instead
    #   of the epoch head
    def __init__(self, parent_hash: bytes, transactions: TransactionList,
                 owner_pubkey: bytes, signed_node_hash: bytes,
                 round: int, index: int, ticket_number: int):
        self.parent_hash = parent_hash
        self.owner_pubkey = owner_pubkey
        self.signed_node_hash = signed_node_hash
        self.round = round
        self.index = index
        self.transactions = transactions
        self.ticket_number = ticket_number

        # TODO: TransactionList should implement a get_hash() function
        self.transaction_hash = transactions.get_hash()

        self.node_hash = self.calculate_node_hash()
        self.proof_hash = self.calculate_proof_hash()
        self.hash = self.calculate_hash()

    def calculate_node_hash(self):
        # TODO: document somewhere that we're representing the
        # round number and block index as little-endian uint32_t
        # TODO: document that we're using the owner_pubkey as the ID
        return sha256(self.owner_pubkey +
                      self.round.to_bytes(4, "little", signed=False) +
                      self.parent_hash).digest()

    def calculate_proof_hash(self):
        return sha256(self.node_hash +
                      self.ticket_number.to_bytes(4, "little", signed=False)).digest()

    def calculate_hash(self) -> bytes:
        return sha256(self.proof_hash + self.parent_hash + self.transaction_hash).digest()

    def __str__(self):
        return f"Block(hash={self.hash.hex()}, parent={self.parent_hash.hex()}, owner={self.owner_pubkey.hex()}, round={self.round}, index={self.index})"


class GenesisBlock(Block):
    def __init__(self, timestamp=None):
        self.hash = b"\x00"
        self.parent_hash = b"\x00"
        self.owner_id = b"\x00"
        self.owner_pubkey = b"\x00"
        self.round = 0
        self.index = 0
        self.epoch_head_hash = b"\x00"
        self.timestamp = timestamp if timestamp is not None else time()

    def __str__(self):
        return (
            f"GenesisBlock(hash={self.hash.hex()}, parent={self.parent_hash.hex()}, "
                         f"owner={self.owner_pubkey.hex()}, round={self.round}, "
                         f"index={self.index}, timestamp={self.timestamp})"
        )
