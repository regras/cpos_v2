from cpos.core.block import Block, GenesisBlock
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.core.blockchain import BlockChain, BlockChainParameters
from cpos.core.transactions import TransactionList
from typing import Optional

# NOT ADAPTED TO CURRENT CODE
# The blockchain atribute "blocks" was substituted by the blockchain database

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
                  round=1,
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

def test_merge():
    # p = tau/total_stake = 1, so we're guaranteed
    # to generate blocks
    params = BlockChainParameters(round_time = 15.0,
                                  tolerance = 2,
                                  tau = 1,
                                  total_stake = 1)

    bc = BlockChain(params)

    key = bytes.fromhex("e41d3e2c7962025f5fa475ec31f3ff6ee5e0a347efffc8e097d854987127b9a3")
    privkey = Ed25519PrivateKey.from_private_bytes(key)
    pubkey = privkey.public_key()
    tx = TransactionList()

    def generate_new_block(bc: BlockChain, parent: Optional[Block] = None, round: Optional[int] = None) -> Block:
        if parent is None:
            parent = bc.blocks[-1]

        if round is None:
            round = parent.round + 1

        new_block = Block(parent_hash=parent.hash,
                      transactions=tx,
                      owner_pubkey=pubkey.public_bytes_raw(),
                      signed_node_hash=b"",
                      round=round+1,
                      index=parent.index+1,
                      ticket_number=1)
        new_block.signed_node_hash = privkey.sign(new_block.node_hash)
        return new_block
    
    new_block = generate_new_block(bc)
    bc.insert(new_block)
    assert len(bc.blocks) == 2

    ancestor = bc.blocks[-1]

    # generate local chain
    for _ in range(3):
        new_block = generate_new_block(bc)
        print(new_block)
        bc.current_round = new_block.round
        bc.insert(new_block)

    # round=3 will generate a better fork
    print("generating fork")
    round = 3
    fork_block = generate_new_block(bc, parent=ancestor, round=round)
    assert fork_block.proof_hash < bc.blocks[2].proof_hash

    fork_subchain = [fork_block]
    for _ in range(3):
        round += 1
        new_block = generate_new_block(bc, parent=fork_subchain[-1], round=round)
        print(new_block)
        fork_subchain.append(new_block)

    bc.merge(fork_subchain)
    print(bc.blocks)
    # confirm whether we inserted the whole fork
    assert bc.blocks[-1] == fork_subchain[-1]


