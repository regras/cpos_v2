from __future__ import annotations
from hashlib import sha256
from cpos.core.transactions import TransactionList

class Block:
    def __init__(self, parent: Block, epoch_head: Block, transactions: TransactionList,
                 owner_id: bytes, owner_pubkey: bytes,
                 round: int, index: int, ticket_number: int):
        self.parent_hash = parent.hash
        self.epoch_head_hash = epoch_head.hash
        self.owner_id = owner_id
        self.owner_pubkey = owner_pubkey
        self.round = round
        self.index = index
        self.transactions = transactions
        self.ticket_number = ticket_number

        # TODO: calculate merkle root from raw transaction data (?)
        self.merkle_root = b"\x00"

        self.node_hash = self.node_hash()
        self.proof_hash = self.calculate_proof_hash()
        self.hash = self.calculate_hash()

    def calculate_node_hash(self):
        # TODO: document somewhere that we're representing the
        # round number and block index as little-endian uint32_t
        return sha256(self.owner_id +
                      self.round.to_bytes(4, "little", signed=False) +
                      self.epoch_head_hash).digest()

    def calculate_proof_hash(self):
        return sha256(self.node_hash +
                      self.ticket_number.to_bytes(4, "little", signed=False)).digest()

    def calculate_hash(self) -> bytes:
        return sha256(self.proof_hash + self.parent_hash + self.merkle_root).digest()


class GenesisBlock(Block):
    def __init__(self):
        self.hash = b"\x00"
        self.parent_hash = b"\x00"
        self.owner_id = b"\x00"
        self.owner_pubkey = b"\x00"
        self.round = 0
        self.index = 0
        self.epoch_head_hash = b"\x00"


if __name__ == "__main__":
    gen = GenesisBlock()
    b = Block(parent = gen,
              epoch_head = gen,
              transactions = None,
              owner_id = b"test",
              owner_pubkey = b"testkey",
              round = 1,
              index = 1)
    hash = b.node_hash()
    print(hash)
