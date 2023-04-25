from cpos.util.merkle import _is_power_of_two, MerkleTree

def test_is_power_of_two():
    assert _is_power_of_two(256) == True

def test_is_not_power_of_two():
    assert _is_power_of_two(255) == False

def test_zero_is_not_power_of_two():
    assert _is_power_of_two(0) == False

def test_merkle_padding():
    # 220 bytes, with chunk_size = 32 -> 7 chunks,
    # should insert zero padding at the end (8 chunks total)
    data = bytes([0xFF] * 220)
    merkle = MerkleTree(data, chunk_size=32)
    assert len(merkle.chunks) == 8
    assert merkle.chunks[-1] == b'\x00'

def test_different_data_merkle_root():
    data1 = bytes([0xFF] * 220)
    data2= bytes([0xFF] * 221)
    merkle1 = MerkleTree(data1, chunk_size=32)
    merkle2 = MerkleTree(data2, chunk_size=32)
    assert merkle1 != merkle2

def test_different_data_padding_merkle_root():
    data1 = bytes([0xFF] * 220)
    data2 = data1 + b"\x00"
    merkle1 = MerkleTree(data1, chunk_size=32)
    merkle2 = MerkleTree(data2, chunk_size=32)
    assert merkle1 != merkle2
