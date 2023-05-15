from cpos.core.sortition import binomial, cumulative_binom_dist, run_sortition
from cpos.core.block import Block, GenesisBlock
from cpos.core.transactions import TransactionList
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashlib import sha256
import pytest
import matplotlib.pyplot as plt

def test_binomial():
    assert binomial(1, 0) == 1
    assert binomial(1, 1) == 1
    assert binomial(123, 1) == 123
    assert binomial(6, 3) == 20
    with pytest.raises(ValueError) as _:
        binomial(5, 6)

def test_cumulative_binom_dist():
    error = abs(cumulative_binom_dist(120, 120, 0.1) - 1.0)
    assert error < 1e-8

@pytest.mark.skip(reason="for visual inspection only")
def test_total_ticket_distribution():
    gen = GenesisBlock()
    transactions = TransactionList()
    b = Block(parent_hash = gen.hash,
              transactions = transactions,
              owner_pubkey = b"testkey",
              round = 1,
              index = 1,
              ticket_number = 1)

    results = []
    total_tickets = 0
    desired_tickets = 10
    node_count = 100
    stake = 3
    p = desired_tickets / (node_count * stake)
    test_run_count = 1000
    for _ in range(test_run_count):
        for i in range(node_count):
            priv = Ed25519PrivateKey.generate()
            signed_node_hash = priv.sign(b.node_hash)
            # TODO: understand why the last byte of the signature is small
            # print(signed_node_hash.hex())
            # print(f"length: {len(signed_node_hash)}")
            successes = run_sortition(signed_node_hash, stake, p)
            if successes > 0:
                print(f"node no. {i} ({priv.public_key().public_bytes_raw().hex()})")
            total_tickets += successes
        results.append(total_tickets)
        total_tickets = 0
    print(results)
    plt.hist(results)
    plt.show()

@pytest.mark.skip(reason="for visual inspection only")
def test_ticket_distribution():
    gen = GenesisBlock()
    transactions = TransactionList()
    priv = Ed25519PrivateKey.generate()
    block = Block(parent_hash = gen.hash,
              transactions = transactions,
              owner_pubkey = b"testkey",
              round = 1,
              index = 1,
              ticket_number = 1)

    results = []
    total_tickets = 0
    desired_tickets = 10
    node_count = 100
    stake = 3
    p = desired_tickets / (node_count * stake)
    test_run_count = 100000
    for _ in range(test_run_count):
        signed_node_hash = priv.sign(block.node_hash)
        hash = sha256(signed_node_hash).digest()
        bit_length = len(hash) * 8
        numerical_hash = int.from_bytes(hash, byteorder="little", signed=False)
        q = numerical_hash / (1 << bit_length)
        results.append(q)
        print(block)
        block = Block(parent_hash = block.hash,
                  transactions = transactions,
                  owner_pubkey = b"testkey",
                  round = block.round + 1,
                  index = block.index + 1,
                  ticket_number = 1)
    plt.hist(results)
    plt.show()

if __name__ == "__main__":
    # test_total_ticket_distribution()
    test_ticket_distribution()
