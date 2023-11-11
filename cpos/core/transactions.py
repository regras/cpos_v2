from __future__ import annotations
import base64
import mysql.connector
import pickle

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
RETRIEVE_QUERY = "SELECT * FROM transactions WHERE committed = 0 and chosen = 0 ORDER BY valuec DESC LIMIT 1"
PATCH_QUERY = "UPDATE transactions SET chosen = 1 WHERE transaction_id = %s"

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
            cursor.execute(RETRIEVE_QUERY)
            self.result = cursor.fetchone()

            if self.result:
                cursor.execute(PATCH_QUERY, (self.result[0],))
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

    def get_hash(self) -> bytes:
        hash_bytes = bytes.fromhex(self.result[6])
        return base64.b64encode(hash_bytes).decode('utf-8')
