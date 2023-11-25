from __future__ import annotations
import base64
import mysql.connector
import pickle
import sys

class TransactionList:
    def __init__(self):
        self.data = b""
        pass
    def serialize(self) -> bytes:
        pass
    @classmethod
    def deserialize(cls, raw: bytes) -> TransactionList:
        pass
    def get_hash(self) -> bytes:
        return b"\x00"

# generating random bytes: https://bobbyhadz.com/blog/python-generate-random-bytes
# encoding binary data with base64: https://stackabuse.com/encoding-and-decoding-base64-strings-in-python/
# working with JSON in python: https://www.freecodecamp.org/portuguese/news/ler-arquivos-json-em-python-como-usar-load-loads-e-dump-dumps-com-arquivos-json/
# workflow: generate random bytes -> convert to base64 -> serialize to JSON
HOST = "localhost"
USER = "CPoS"
PASSWORD = "CPoSPW"
DATABASE = "mempool"
RETRIEVE_QUERY = "SELECT * FROM transactions WHERE committed = 0 and chosen = 0 ORDER BY value DESC LIMIT 1"
PATCH_QUERY = "UPDATE transactions SET chosen = 1 WHERE transaction_id = %s"
BLOCK_SIZE = 199000     # 200kb - ~1kB of header

class MockTransactionList(TransactionList):
    def __init__(self):
        try:
            connection = mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )
            cursor = connection.cursor()

            self.transactions = []
            totalSize = 0

            while totalSize < BLOCK_SIZE:
                cursor.execute(RETRIEVE_QUERY)
                result = cursor.fetchone()
                totalSize += sum([sys.getsizeof(result[tuplePosition]) for tuplePosition in range(len(result))])
                if totalSize > BLOCK_SIZE:
                    break

                self.transactions.append(result)

                if result:
                    cursor.execute(PATCH_QUERY, (result[0],))
                    connection.commit()

            cursor.close()

        except mysql.connector.Error as err:
            print(f"Error: {err}")
    
        finally:
            if 'connection' in locals():
                connection.close()
                print("Connection closed!")

    def serialize(self) -> bytes:
        tx_raw = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        return tx_raw

    @classmethod
    def deserialize(cls, raw: bytes) -> TransactionList:
        return pickle.loads(raw)

    #TODO: get hash of all transactions (probably using Merkle tree)
    def get_hash(self) -> bytes:
        if self.transactions:
            hash_bytes = bytes.fromhex(self.transactions[0][6])
            return base64.b64encode(hash_bytes)
        else:
            return b"\x00"
