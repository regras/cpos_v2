from hashlib import sha256

def _is_power_of_two(n: int) -> bool:
    return (n & (n-1)) == 0 and n != 0

# calculate padding necessary to round n up to the next power of 2
def _calculate_padding(n: int):
    if _is_power_of_two(n):
        return 0
    else:
        # TODO: could probably be done more efficiently with binary operations
        return (1 << n.bit_length()) - n

# https://github.com/bitcoin/bips/blob/master/bip-0098.mediawiki
class MerkleTree:
    def __init__(self, data: bytes, chunk_size: int = 8192):
        if not data:
            raise TypeError("MerkleTree input data cannot be empty")
        self.data = data
        self.chunk_size = chunk_size
        self.chunks = self._create_hashed_chunks()
        self._insert_padding()

    def _create_hashed_chunks(self) -> list[bytes]:
        size = len(self.data)
        chunks = []
        for offset in range(0, size, self.chunk_size):
            start = offset
            end = offset + self.chunk_size
            chunk = sha256(self.data[start:end]).digest()
            chunks.append(chunk)
        return chunks

    """
    Insert zero padding at the end of the chunk list so that
    its size is a power of two
    """
    def _insert_padding(self):
        if not _is_power_of_two(len(self.chunks)):
            padding = _calculate_padding(len(self.chunks))
            self.chunks += [bytes([0x00])] * padding

    def merkle_root(self) -> bytes:
        def get_index(i: int, round: int):
            return i * (1 << round)
        size = len(self.chunks)
        round = 0
        t = self.chunks
        while size > 1:
            # somewhat ugly solution, could probably be improved
            for i in range(0, size, 2):
                first = get_index(i, round)
                second = get_index(i+1, round)
                hash = sha256(t[first] + t[second])
                t[first]= hash.digest()
                pass
            size >>= 1  # size /= 2
            round += 1
        return t[0]
