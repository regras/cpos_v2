from cpos.core.block import Block, GenesisBlock
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.core.blockchain import BlockChain, BlockChainParameters
from cpos.core.transactions import TransactionList

# TODO: maybe split these into smaller tests
def test_basic_insertion():
    params = BlockChainParameters(round_time = 15.0,
                                  tolerance = 2,
                                  tau = 2,
                                  total_stake = 10)
    bc = BlockChain(params)

    # this key will pass the sortition
    key = bytes.fromhex("af50c32e180b96b3c44b6cd7232f581ba73912893c23314afbee3f299a30cec7")
    privkey = Ed25519PrivateKey.from_private_bytes(key)
    pubkey = privkey.public_key()
    tx = TransactionList()
    block = Block(parent_hash=bc.genesis.hash,
                  transactions=tx,
                  owner_pubkey=pubkey.public_bytes_raw(),
                  signed_node_hash=b"",
                  round=0,
                  index=1,
                  ticket_number=1)
    block.signed_node_hash = privkey.sign(block.node_hash)

    # fail because there is a gap
    block.index = 2
    assert bc.insert(block) == False
    block.index = 1

    # fail because our ticket_number is too large
    block.ticket_number = 10
    assert bc.insert(block) == False
    block.ticket_number = 1

    # fail because our parent hash is wrong
    block.parent_hash = b"\xFF"
    assert bc.insert(block) == False
    block.parent_hash = bc.genesis.hash

    # fail because the signed_node_hash is wrong
    original_signed_node_hash = block.signed_node_hash
    block.signed_node_hash = b""
    assert bc.insert(block) == False
    block.signed_node_hash = original_signed_node_hash

    # reject blocks beyond our tolerance limit
    block.round = 5
    assert bc.insert(block) == False
    block.round = 0

    # now actually try inserting the original, valid block
    assert bc.insert(block) == True

    # trying to insert again should fail
    assert bc.insert(block) == False

def test_failed_insertion():
    params = BlockChainParameters(round_time = 15.0,
                                  tolerance = 2,
                                  tau = 2,
                                  total_stake = 10)
    bc = BlockChain(params)

    # this key will fail the sortition
    key = bytes.fromhex("e41d3e2c7962025f5fa475ec31f3ff6ee5e0a347efffc8e097d854987127b9a3")
    privkey = Ed25519PrivateKey.from_private_bytes(key)
    print(privkey.private_bytes_raw().hex())
    pubkey = privkey.public_key()
    tx = TransactionList()
    block = Block(parent_hash=bc.genesis.hash,
                  transactions=tx,
                  owner_pubkey=pubkey.public_bytes_raw(),
                  signed_node_hash=b"",
                  round=0,
                  index=1,
                  ticket_number=1)
    block.signed_node_hash = privkey.sign(block.node_hash)

    assert bc.insert(block) == False 

