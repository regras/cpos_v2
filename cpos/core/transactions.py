from __future__ import annotations
import base64
import mysql.connector
import pickle
import sys

class TransactionList:
    def __init__(self):
        self.data = b""
        self.transactions = str([])
        pass
    def serialize(self) -> bytes:
        pass
    @classmethod
    def deserialize(cls, raw: bytes) -> TransactionList:
        pass
    def get_hash(self) -> bytes:
        return b"\x00"
    def set_transactions(self, transactions: str):
        self.transactions = transactions

# generating random bytes: https://bobbyhadz.com/blog/python-generate-random-bytes
# encoding binary data with base64: https://stackabuse.com/encoding-and-decoding-base64-strings-in-python/
# working with JSON in python: https://www.freecodecamp.org/portuguese/news/ler-arquivos-json-em-python-como-usar-load-loads-e-dump-dumps-com-arquivos-json/
# workflow: generate random bytes -> convert to base64 -> serialize to JSON
HOST = "localhost"
USER = "CPoS"
PASSWORD = "CPoSPW"
DATABASE = "mempool"
# This retrieve query has a limit of 200 for memory safety purposes. You can change if you want.
# This number was chosen considering we had at most 110 transactions during our tests for theses parameters.
RETRIEVE_QUERY = "SELECT * FROM transactions WHERE committed = 0 and chosen = 0 ORDER BY value DESC LIMIT 200"
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
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute(RETRIEVE_QUERY)

            self.transactions_list = []
            transaction_ids = []
            totalSize = 0

            result_set = cursor.fetchall()

            for row in result_set:
                totalSize += sum([sys.getsizeof(row[tuplePosition]) for tuplePosition in row.keys()])
                if totalSize > BLOCK_SIZE:
                    break
                self.transactions_list.append(row)
                transaction_ids.append(row['transaction_id'])

            format_strings = ','.join(['%s'] * len(transaction_ids))
            PATCH_QUERY = f"UPDATE transactions SET chosen = 1 WHERE transaction_id IN ({format_strings})"
            cursor.execute(PATCH_QUERY, transaction_ids)
            connection.commit()

            cursor.close()

            self.transactions = str(self.transactions_list)

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
    
    def set_transactions(self, transactions: str):
        self.transactions = transactions

    #TODO: get hash of all transactions (probably using Merkle tree)
    def get_hash(self) -> bytes:
        return b"\x00" # TODO Provisory, code below does not work
        if self.transactions:
            hash_bytes = bytes.fromhex(self.transactions[0]["transaction_hash"])
            return base64.b64encode(hash_bytes)
        else:
            return b"\x00"
    
    
