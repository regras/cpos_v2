from cpos.protocol.messages import Hello, BlockBroadcast
from cpos.core.block import Block, GenesisBlock
from cpos.core.transactions import TransactionList
import pytest

def test_hello_serialization():
    assert True

def test_block_broadcast_serialization():
    gen = GenesisBlock()
    transactions = TransactionList()
    b = Block(parent_hash = gen.hash,
              transactions = transactions,
              owner_pubkey = b"testkey",
              signed_node_hash = b"1234",
              round = 1,
              index = 1,
              ticket_number = 1)
    original = Block(parent_hash = b.hash,
                     transactions = transactions,
                     owner_pubkey = b"testkey2",
                     signed_node_hash = b"12345",
                     round = 2,
                     index = 2,
                     ticket_number = 1)
    msg = BlockBroadcast(original)
    deserialized = BlockBroadcast.deserialize(msg.serialize()).block
    assert original.hash == deserialized.hash
    assert original.parent_hash == deserialized.parent_hash
    assert original.owner_pubkey == deserialized.owner_pubkey
    assert original.transaction_hash == deserialized.transaction_hash
    assert original.round == deserialized.round
    assert original.index == deserialized.index
    assert original.ticket_number == deserialized.ticket_number
