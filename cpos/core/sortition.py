from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from hashlib import sha256
from cpos.core.block import GenesisBlock, Block
from cpos.core.transactions import TransactionList

# n*(n-1)*...*(n-p+1) / p*(p-1)*...*1
# TODO: maybe memoize this (store several values in a table?)
def binomial(n: int, p: int):
    if p > n:
        raise ValueError(f"Invalid binomial coefficient: binomial({n}, {p})")
    numerator = 1
    for i in range(n, n-p, -1):
        numerator *= i
    denominator = 1
    for i in range(2, p+1):
        denominator *= i
    return numerator/denominator

def cumulative_binom_dist(n: int, k: int, p: float) -> float:
    # TODO: handle overflow errors here
    sum = 0
    for i in range(0, k+1):
        sum += binomial(n, i) * (p ** i) * ((1-p) ** (n-i))
    return sum

"""Runs a sortition.

Args:
    signed_node_hash: Bytes object containing the signature of the node hash.
    stake: Integer representing the number of invested stakes.
    success_probability: Float representing the chance of having at least one selected ticket in the sortition.

Returns:
    An integer representing the number of selected tickets in the sortition. It is, at most, the number of stakes invested.

"""
def run_sortition(signed_node_hash: bytes, stake: int,
                  success_probability: float) -> int:
    hash = sha256(signed_node_hash).digest()
    bit_length = len(hash) * 8
    numerical_hash = int.from_bytes(hash, byteorder="little", signed=False)

    q = numerical_hash / (1 << bit_length)
    # print(q)

    i = 0
    while q > cumulative_binom_dist(stake, i, success_probability):
        # print(f"i = {i}, q > cumulative_binom_dist({stake}, {i}, {success_probability}) = {cumulative_binom_dist(stake, i , success_probability)}")
        i += 1

    # print(f"result: {i}")
    return i

def main():
    gen = GenesisBlock()
    transactions = TransactionList()
    b = Block(parent = gen,
              transactions = transactions,
              owner_pubkey = b"testkey",
              round = 1,
              index = 1,
              ticket_number = 1)

    total_tickets = 0
    desired_tickets = 2
    node_count = 10000
    stake = 3
    p = desired_tickets / (node_count * stake)
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
    print(f"total tickets: {total_tickets}")

if __name__ == "__main__":
    main()
