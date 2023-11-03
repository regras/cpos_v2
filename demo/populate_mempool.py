import base64
import datetime
import hashlib
import mysql.connector
import numpy as np
import os
import signal

from time import sleep

HOST = "localhost"
USER = "CPoS"
PASSWORD = "CPoSPW"
DATABASE = "mempool"
INSERT_QUERY = "INSERT INTO transactions (transaction_id, value, input_address, output_address, committed, choosen, transaction_hash, data, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

PROGRAM_INTERRUPTED = False

def sighandler(*args):
    global PROGRAM_INTERRUPTED 
    PROGRAM_INTERRUPTED = True

class RandomTransactionGenerator:
    def __init__(self) -> None:
        self.transaction_id = 0
        self.input_address = self.generate_random_string(256)
        self.output_address = self.generate_random_string(256)
        self.committed = 0
        self.choosen = 0

    def generate_random_transactions(self) -> tuple:
        value = np.random.normal(100,20)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        data = self.generate_random_string(int(np.random.normal(100, 20)))

        transaction_hash = self.generate_hash(
            str(self.transaction_id) +
            str(value) +
            str(self.input_address) +
            str(self.output_address) +
            str(self.committed) +
            str(self.choosen) +
            str(data) +
            str(timestamp)
        )

        transaction = (
            self.transaction_id,
            value,
            self.input_address,
            self.output_address,
            self.committed,
            self.choosen,
            transaction_hash,
            data,
            timestamp
        )

        self.transaction_id += 1

        return transaction

    def generate_hash(self, data:str) -> str:
        sha = hashlib.sha256()
        sha.update(base64.b64encode(data.encode('utf-8')))
        return sha.hexdigest()
    
    def generate_random_string(self, length:int) -> str:
        random_bytes = os.urandom(length)
        random_string = hashlib.sha256(random_bytes).hexdigest()
        return random_string[:length]

def populate_mempool() -> None:
    try:
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )

        if connection.is_connected():
            print("Connected to the MariaDB database!")

        generator = RandomTransactionGenerator()

        while not PROGRAM_INTERRUPTED:
            transaction = generator.generate_random_transactions()
            cursor = connection.cursor()
            cursor.execute(INSERT_QUERY, transaction)
            connection.commit()
            cursor.close()
            sleep(0.01)

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    
    finally:
        if 'connection' in locals():
            connection.close()
            print("Connection closed!")

if __name__ == "__main__":
    populate_mempool()
