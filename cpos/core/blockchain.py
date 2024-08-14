import base64
import datetime
import hashlib
import mysql.connector
import numpy as np
import os
import signal
from time import sleep
from cpos.core.block import Block, GenesisBlock
from cpos.core.transactions import TransactionList, MockTransactionList
from cpos.core.sortition import fork_threshold, run_sortition, confirmation_threshold
from time import time
from typing import Optional
from collections import OrderedDict
import logging
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


HOST = "localhost"
USER = "CPoS"
PASSWORD = "CPoSPW"
DATABASE = "localBlockchain"
PROGRAM_INTERRUPTED = False

try:
    connection = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE
    )

    if connection.is_connected():
        print("Connected to the MariaDB database!")

except mysql.connector.Error as err:
    print(f"Error: {err}")

def sighandler(*args):
    global PROGRAM_INTERRUPTED 
    PROGRAM_INTERRUPTED = True

class BlockChainParameters:
    def __init__(self, round_time: float, tolerance: int, tau: int, total_stake=10):
        self.round_time = round_time
        self.tolerance = tolerance
        self.tau = tau
        self.total_stake = total_stake
        pass


class BlockChain:

    def __init__(self, parameters: BlockChainParameters, genesis: Optional[GenesisBlock] = None, node_id: bytes = None):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: [{node_id.hex()[0:8]}] %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger
        
        self.parameters: BlockChainParameters = parameters

        if genesis is not None:
            self.genesis: GenesisBlock = genesis
        else:
            self.genesis: GenesisBlock = GenesisBlock()
        
        self.insert_genesis_block(genesis, 0, 1) # TODO CHECK ARRIVE TIME OF GENESIS BLOCK, genesis block is altomatically confirmed
        # TODO: this stores the number of successful sortitions that have
        # a certain block into the foreign blockchain view; document/find
        # better naming later
        self.last_confirmation_delay: int = 0
        self.fork_detected = False

        self.current_round: int = 0
        self.update_round()

    def update_round(self):
        current_time = time()
        genesis_time = self.genesis.timestamp
        delta_t = current_time - genesis_time
        round = int(delta_t / self.parameters.round_time)

        if self.current_round == round:
            return

        self.current_round = round

        self.logger.info(f"starting round {round}")
        self._dump_block_hashes()

        # verify whether we can confirm the oldest unconfirmed block or
        # whether a fork has been detected
        # (this fork detection logic really, REALLY needs to be its own class)

        # should only happen if the chain only has the genesis block
        last_confirmed_block_index, last_confirmed_block_id, last_confirmed_block_round = self.last_confirmed_block_info()

        if last_confirmed_block_id == self.last_block_id(): 
            return

        oldest_index, oldest_id, oldest_numSuc, oldest_round = self.oldest_unconfirmed_block()
        delta_r = round - oldest_round

        if delta_r > 0 and oldest_index > 0:
            successful_avg = oldest_numSuc / delta_r
            self.logger.info(f"oldest unconfirmed block: {oldest_id}, delta_r: {delta_r}, s: {successful_avg}")

            # TODO: make the epsilon threshold variable
            conf_thresh = confirmation_threshold(total_stake=self.parameters.total_stake,
                                   tau=self.parameters.tau,
                                   delta_r=delta_r,
                                   threshold=1e-6)
            self.logger.info(f"s_min: {conf_thresh}")

            if successful_avg > conf_thresh:
                self.logger.info(f"confirmed block {oldest_id}")
                self.confirm_block(oldest_id)
                self.last_confirmation_delay = self.current_round - last_confirmed_block_round 

            fork_thresh = fork_threshold(total_stake=self.parameters.total_stake,
                                   tau=self.parameters.tau,
                                   delta_r=delta_r,
                                   threshold=0.95)

            if successful_avg < fork_thresh:
                self.fork_detected = True
                self.logger.info(f"fork detected!")

    def _log_failed_verification(self, block: Block, reason: str):
        self.logger.debug(f"failed to verify block {block.hash.hex()} ({reason})")

    # TODO: these two are stubs, we need to implement an actual search
    # through the blockchain transactions later
    def lookup_node_stake(self, node_id: bytes) -> int:
        return 1
    def lookup_total_stake(self) -> int:
        return self.parameters.total_stake

    def validate_block(self, block: Block) -> Optional[int]:
        pubkey = None
        try:
            pubkey = Ed25519PublicKey.from_public_bytes(block.owner_pubkey)
        except ValueError:
            self._log_failed_verification(block, "bad pubkey")
            return None
        
        try:
            pubkey.verify(block.signed_node_hash, block.node_hash)
        except InvalidSignature:
            self._log_failed_verification(block, "bad node_hash signature")
            return None

        stake = self.lookup_node_stake(block.owner_pubkey)
        total_stake = self.lookup_total_stake()
        success_probability = self.parameters.tau / total_stake
        winning_tickets = run_sortition(block.signed_node_hash, stake, success_probability)
        self.logger.debug(f"ran sortition for block {block.hash.hex()[0:7]} (p = {success_probability}); result = {winning_tickets}") 
        if winning_tickets == 0 or winning_tickets < block.ticket_number:
            self._log_failed_verification(block, "sortition failed")
            return None
        
        return winning_tickets

    def _log_failed_insertion(self, block: Block, reason: str):
        self.logger.info(f"discarding block {block.hash.hex()} ({reason})")

    def set_genesis_block(self, genesis: GenesisBlock) -> bool: # UNUSED
        cursor = connection.cursor()
        CHECK_NON_EMPTY_TABLE_QUERY = "SELECT EXISTS (SELECT 1 FROM localChains)" # returns (1,) or (0,)
        cursor.execute(CHECK_NON_EMPTY_TABLE_QUERY)
        for i in cursor: # Can be more clear with cursor.fetchone
            if (i==(1,)): # already a block in the blockchain
                self.logger.error(f"refusing to insert new genesis block")
                return False
        self.insert_genesis_block(genesis, 0, 1) # TODO CHECK ARRIVE TIME OF GENESIS BLOCK
        connection.commit()
        cursor.close()

        return True
    
    # try to insert a block at the end of the chain
    def insert(self, block: Block) -> bool:

        if self.block_in_blockchain(block):
            self._log_failed_insertion(block, "already in local chain")

        if block.index == 0:
            self._log_failed_insertion(block, "new genesis block")
            return False
        
        if block.index > self.number_of_blocks():
            self._log_failed_insertion(block, "gap in local chain")
            return False

        if not self.has_correct_parent(block):
            self._log_failed_insertion(block, f"parent mismatch")
            return False

        winning_tickets = self.validate_block(block)
        if not winning_tickets:
            self._log_failed_insertion(block, "validation failed")
            return False
        else:
            self.update_successfull_sortition(block.index, winning_tickets)

        # in case there is already a block present at block.index
        if self.number_of_blocks() > block.index:
            if block.proof_hash <= self.get_proof_hash_of_block(block.index):
                self._log_failed_insertion(block, f"smaller proof_hash")
                return False
        
        # reject block if it was added in the same round as the parent
        parent_idx = block.index - 1

        if block.round <= self.get_round_of_block(parent_idx):
            self._log_failed_insertion(block, "same round as parent")
            return False
        
        self.logger.info(f"inserting {block}")
        self.delete_blocks_since(block.index)
        self.insert_block(block, time(), 0) # TODO CHECK ARRIVAL TIME
        return True

    def merge(self, foreign_blocks: list[Block]) -> bool:
        self.logger.info(f"starting merge process with fork: {foreign_blocks}")
        first_foreign_block = foreign_blocks[0]

        id_and_idx = self.block_of_hash(first_foreign_block.parent_hash)

        if id_and_idx is None:
            self.logger.error(f"foreign subchain has no common ancestor with local chain")
            return False
        
        id, idx = id_and_idx

        self.logger.info(f"found common ancestor: {id}")  
        # temporarily remove local fork from the chain
        # TODO from this point this function seems very optimizable
        original_local_subchain = self.blocks_since_index(idx + 1)
        self.delete_blocks_since(idx+1)

        # try inserting the head of the fork
        if not self.insert(foreign_blocks.pop(0)):
            self.logger.info(f"merge failed: foreign chain is worse than local chain")
            self.reintroduce_blocks(original_local_subchain)
            return False
        # if successful, try inserting all following blocks
        else:
            self.logger.info(f"merge success")
            for block in foreign_blocks:
                if not self.insert(block):
                    break

        return True

    def _dump_state(self):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM localChains ORDER BY block_index ASC")
        for block in cursor:
            print(block)
        connection.commit()
        cursor.close()

    def _dump_indexes(self):
        cursor = connection.cursor()
        cursor.execute("SELECT block_index FROM localChains ORDER BY block_index ASC")
        for index in cursor:
            print(index)
        connection.commit()
        cursor.close()
    
    def _dump_block_hashes(self):
        block_hashes = []
        cursor = connection.cursor()
        cursor.execute("SELECT hash FROM localChains ORDER BY block_index ASC")
        for hash in cursor:
            block_hashes.append(hash[0][0:min(len(hash[0]),8)])
        connection.commit()
        cursor.close()
        self.logger.info(f"current chain: {block_hashes}")

    def insert_block(self, block: Block, arrive_time: int, confirmed: int):
        database_atributes = [block.index, block.hash.hex(), block.round, block.parent_hash.hex(), block.hash.hex(), block.owner_pubkey.hex(), block.signed_node_hash.hex(), block.transaction_hash.hex(), block.ticket_number,
                            block.transactions, arrive_time, 0, confirmed, 0, block.proof_hash.hex(), 0, 0] # TODO hash as id? TODO implement real merkle tree
        cursor = connection.cursor()
        INSERT_QUERY = "INSERT INTO localChains (block_index, id, round, parent_hash, hash, owner_pubkey, signed_node_hash, merkle_root, ticket_number, transactions, arrive_time, fork, confirmed, subuser, proof_hash, numSuc, round_stable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(INSERT_QUERY, database_atributes)
        connection.commit()
        cursor.close()

    def compose_block(self, block_info):
        # Receives a line from the database containing block info and returns a block with that info
        transaction_list = TransactionList()
        transaction_list.set_transactions(block_info[9])
        b = Block(parent_hash=bytes.fromhex(block_info[3]),
                owner_pubkey=bytes.fromhex(block_info[5]), 
                signed_node_hash=bytes.fromhex(block_info[6]), 
                round=block_info[2],
                index=block_info[0],
                transactionlist=transaction_list, 
                ticket_number=block_info[8])
        return b

    def insert_genesis_block(self, block: Block, arrive_time: int, confirmed: int):
        database_atributes = [block.index, block.hash.hex(), block.round, block.parent_hash.hex(), block.hash.hex(), block.owner_pubkey.hex(), block.signed_node_hash.hex(), block.transaction_hash.hex(), block.ticket_number,
                              str([]), arrive_time, 0, confirmed, 0, block.proof_hash.hex(), 0, 0] # TODO hash as id? TODO implement real merkle tree
        cursor = connection.cursor()
        self.logger.info(str(int.from_bytes(block.hash)))
        INSERT_QUERY = "INSERT INTO localChains (block_index, id, round, parent_hash, hash, owner_pubkey, signed_node_hash, merkle_root, ticket_number, transactions, arrive_time, fork, confirmed, subuser, proof_hash, numSuc, round_stable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(INSERT_QUERY, database_atributes)
        connection.commit()
        cursor.close()
    
    def block_in_blockchain(self, block: Block):
        FIND_BLOCK_QUERY = "SELECT * FROM localChains WHERE id = %s LIMIT 1" # TODO hash as id?
        cursor = connection.cursor()
        cursor.execute(FIND_BLOCK_QUERY, [block.hash.hex()])
        element = cursor.fetchone()
        block_in_blockchain = (element != None)
        cursor.close()
        return block_in_blockchain
    
    def number_of_blocks(self):
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM localChains")
        count = cursor.fetchone()[0]
        cursor.close()
        return count

    def has_correct_parent(self, block: Block):
        cursor = connection.cursor()
        cursor.execute(f"SELECT hash FROM localChains WHERE block_index = {block.index - 1}")
        hash = bytes.fromhex(cursor.fetchone()[0])
        cursor.close()
        return hash == block.parent_hash

    def delete_blocks_since(self, index: int):
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM localChains WHERE block_index >= {index}")
        connection.commit()
        cursor.close()
    
    def last_confirmed_block_info(self):
        cursor = connection.cursor()
        cursor.execute("SELECT block_index, id, round FROM localChains WHERE confirmed = 1 ORDER BY block_index DESC LIMIT 1")
        block_index, id, round = cursor.fetchone()
        cursor.close()
        id = bytes.fromhex(id)
        return block_index, id, round
    
    def last_block_id(self):
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM localChains ORDER BY block_index DESC LIMIT 1")
        id = bytes.fromhex(cursor.fetchone()[0])
        cursor.close()
        return id
    
    def oldest_unconfirmed_block(self):
        cursor = connection.cursor()
        cursor.execute("SELECT block_index, id, numSuc, round FROM localChains WHERE confirmed = 0 ORDER BY block_index ASC LIMIT 1")
        block_index, id, numSuc, round = cursor.fetchone()
        id = bytes.fromhex(id)
        cursor.close()
        return block_index, id, numSuc, round
    
    def confirm_block(self, id):
        cursor = connection.cursor()
        cursor.execute(f'UPDATE localChains SET confirmed = 1 WHERE id = "{id.hex()}"')
        connection.commit()
        cursor.close()

    def update_successfull_sortition(self, index, winning_tickets):
        cursor = connection.cursor()
        cursor.execute(f"UPDATE localChains SET numSuc = numSuc + {winning_tickets} WHERE block_index < {index} AND confirmed = 0")
        connection.commit()
        cursor.close()

    def get_proof_hash_of_block(self, index):
        cursor = connection.cursor()
        cursor.execute(f"SELECT proof_hash FROM localChains WHERE block_index = {index}")
        proof_hash = bytes.fromhex(cursor.fetchone()[0])
        cursor.close()
        return proof_hash
    
    def get_round_of_block(self, index):
        cursor = connection.cursor()
        cursor.execute(f"SELECT round FROM localChains WHERE block_index = {index}")
        block_round = cursor.fetchone()[0]
        cursor.close()
        return block_round
    
    def contains_in_db(self, block: Block): # TODO hash as id? OPTIMIZABLE WITH SQL COMMAND
        cursor = connection.cursor()
        cursor.execute(f"SELECT hash FROM localChains")
        for h in cursor:
            hash = bytes.fromhex(h)
            if hash == block.hash:
                cursor.close()
                return True
        cursor.close()
        return False
    
    def get_last_block_hash(self): # TODO hash as id?
        cursor = connection.cursor()
        cursor.execute("SELECT hash FROM localChains ORDER BY block_index DESC LIMIT 1")
        block_hash = bytes.fromhex(cursor.fetchone()[0])
        cursor.close()
        return block_hash
    
    def block_of_hash(self, hash):
        # Returns a two element list in format [id, block_index] or None
        cursor = connection.cursor()
        BLOCK_OF_HASH_QUERY = f'SELECT id, block_index FROM localChains WHERE hash = "{hash.hex()}" ORDER BY block_index ASC LIMIT 1'
        cursor.execute(BLOCK_OF_HASH_QUERY)
        info = cursor.fetchone()
        if info != None:
            info = list(info)
            info[0] = bytes.fromhex(info[0])
        cursor.close()
        return info
    
    def blocks_since_index(self, index):
        cursor = connection.cursor()
        blocks_info = []
        cursor.execute(f"SELECT * FROM localChains WHERE block_index >= {index} ORDER BY block_index")
        for i in cursor:
            blocks_info.append(i)
        cursor.close()
        return blocks_info
    
    def reintroduce_blocks(self, list_of_blocks_data):
        cursor = connection.cursor()
        for block_data in list_of_blocks_data:
            INSERT_QUERY = "INSERT INTO localChains (block_index, id, round, parent_hash, hash, owner_pubkey, signed_node_hash, merkle_root, ticket_number, transactions, arrive_time, fork, confirmed, subuser, proof_hash, numSuc, round_stable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(INSERT_QUERY, block_data)
        connection.commit()
        cursor.close()
    
    def last_n_blocks(self, n):
        # Returns in the form of a list of blocks
        cursor = connection.cursor()
        block_list = []
        cursor.execute(f"SELECT * FROM localChains ORDER BY block_index ASC LIMIT {n}")
        for block_info in cursor:
            block_list.append(self.compose_block(block_info))
        cursor.close()
        return block_list

    def block_by_index(self, block_index):
        # Returns in the form of a Block class
        if block_index < 0:
            block_index = self.number_of_blocks() + block_index
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM localChains WHERE block_index = {block_index}")
        block_info = cursor.fetchone()
        cursor.close()
        return self.compose_block(block_info)
