from cpos.protocol.messages import Hello, BlockBroadcast
from cpos.core.block import Block, GenesisBlock
from cpos.core.transactions import TransactionList

def test_hello_serialization():
    assert True

def test_block_broadcast_serialization():
    gen = GenesisBlock()
    transactions = TransactionList()
    b = Block(parent_hash = gen.hash,
              transactions = transactions,
              owner_pubkey = b"testkey",
              round = 1,
              index = 1,
              ticket_number = 1)
    block = Block(parent_hash = b.hash,
                  transactions = transactions,
                  owner_pubkey = b"testkey2",
                  round = 2,
                  index = 2,
                  ticket_number = 1)
    msg = BlockBroadcast(block)
    print(msg.serialize())
    assert False
