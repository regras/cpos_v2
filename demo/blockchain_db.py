import base64
import datetime
import hashlib
import mysql.connector
import numpy as np
import os
import signal
from time import sleep
from cpos.core.block import Block, GenesisBlock
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
    def __contains__(self, block: Block): # OLD
        for b in self.blocks:
            if b.hash == block.hash:
                return True
        return False

    def __init__(self, parameters: BlockChainParameters, genesis: Optional[GenesisBlock] = None):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger
        
        self.blocks: list[Block] = []
        self.parameters: BlockChainParameters = parameters

        try:
            self.connection = mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )

            if self.connection.is_connected():
                self.db_connection_success = True
                print("Connected to the MariaDB database!")

        except mysql.connector.Error as err:
            self.db_connection_success = False
            print(f"Error: {err}")

        if genesis is not None:
            self.genesis: GenesisBlock = genesis
        else:
            self.genesis: GenesisBlock = GenesisBlock()
        
        self.blocks.append(self.genesis)
        # TODO: this stores the number of successful sortitions that have
        # a certain block into the foreign blockchain view; document/find
        # better naming later
        self.unconfirmed_blocks: OrderedDict[Block, int] = OrderedDict()
        self.last_confirmed_block: Block = self.genesis
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
        self.logger.info(f"current chain: {self.blocks}")

        # verify whether we can confirm the oldest unconfirmed block or
        # whether a fork has been detected
        # (this fork detection logic really, REALLY needs to be its own class)

        
        # should only happen if the chain only has the genesis block
        if self.last_confirmed_block == self.blocks[-1]: # OLD
            return
        
        if self.last_confirmed_block_id() == self.last_block_id():
            return

        # oldest unconfirmed block
        oldest = self.blocks[self.last_confirmed_block.index + 1] # OLD
        oldest_index, oldest_id, oldest_numSuc, oldest_round = self.oldest_unconfirmed_block()
        delta_r = round - oldest.round

        if delta_r > 0 and oldest.index > 0: # OLD
            successful_avg = self.unconfirmed_blocks[oldest] / delta_r
            self.logger.info(f"oldest unconfirmed block: {oldest}, delta_r: {delta_r}, s: {successful_avg}")
            # TODO: make the epsilon threshold variable
            conf_thresh = confirmation_threshold(total_stake=self.parameters.total_stake,
                                   tau=self.parameters.tau,
                                   delta_r=delta_r,
                                   threshold=1e-6)
            self.logger.info(f"s_min: {conf_thresh}")
            if successful_avg > conf_thresh:
                self.logger.info(f"confirmed block {oldest}")
                self.last_confirmed_block = self.blocks[oldest.index]
                self.last_confirmation_delay = self.current_round - self.last_confirmed_block.round
                self.unconfirmed_blocks.pop(oldest)

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

                self.last_confirmation_delay = self.current_round - oldest_round

            fork_thresh = confirmation_threshold(total_stake=self.parameters.total_stake,
                                   tau=self.parameters.tau,
                                   delta_r=delta_r,
                                   threshold=0.95)

            if successful_avg < fork_thresh:
                self.fork_detected = True

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

    def set_genesis_block(self, genesis: GenesisBlock) -> bool:
        cursor = self.connection.cursor()
        CHECK_NON_EMPTY_TABLE_QUERY = "SELECT EXISTS (SELECT 1 FROM localChains)" # returns (1,) or (0,)
        cursor.execute(CHECK_NON_EMPTY_TABLE_QUERY)
        for i in cursor:
            if (i==(1,)):
                self.logger.error(f"refusing to insert new genesis block")
                False
        self.insert_block(genesis, 0) # TODO CHECK ARRIVE TIME OF GENESIS BLOCK
        self.connection.commit()
        cursor.close()

        if len(self.blocks) != 0: # OLD
            self.logger.error(f"refusing to insert new genesis block")
            return False

        self.blocks.append(genesis) # OLD
        return True
    
    # try to insert a block at the end of the chain
    def insert(self, block: Block) -> bool:

        if self.block_in_blockchain(block):
            self._log_failed_insertion(block, "already in local chain")

        if block in self: # OLD
            self._log_failed_insertion(block, "already in local chain")

        if block.index == 0:
            self._log_failed_insertion(block, "new genesis block")
            return False 
        
        if block.index > self.number_of_blocks():
            self._log_failed_insertion(block, "gap in local chain")
            return False
        
        if block.index > len(self.blocks):# OLD
            self._log_failed_insertion(block, "gap in local chain")
            return False
        
        if not self.equal_parent_block(block):
            self._log_failed_insertion(block, "parent mismatch")
            return False

        if self.blocks[block.index - 1].hash != block.parent_hash: # OLD
            self._log_failed_insertion(block, "parent mismatch")
            return False

        winning_tickets = self.validate_block(block)
        if not winning_tickets:
            self._log_failed_insertion(block, "validation failed")
            return False
        else:
            # update the successful sortition statistics
            preceding_blocks = self.blocks[0 : block.index] # OLD
            for b in preceding_blocks: # OLD
                if b in self.unconfirmed_blocks: # OLD
                    self.unconfirmed_blocks[b] += winning_tickets # OLD
            self.update_successfull_sortition(block.index, winning_tickets)
            

        # in case there is already a block present at block.index
        if self.number_of_blocks() > block.index:
            if block.proof_hash <= self.get_proof_hash_of_block(block.index):
                self._log_failed_insertion(block, "smaller proof_hash")
                return False

        if len(self.blocks) > block.index: # OLD
            if block.proof_hash <= self.blocks[block.index].proof_hash:
                self._log_failed_insertion(block, "smaller proof_hash")
                return False

        # reject block if it was added in the same round as the parent
        parent_idx = block.index - 1
        if block.round <= self.blocks[parent_idx].round: # OLD
            self._log_failed_insertion(block, "same round as parent")
            return False
        
        if block.round <= self.get_round_of_block(parent_idx):
            self._log_failed_insertion(block, "same round as parent")
            return False

        # self.logger.info(f"s: {self.unconfirmed_blocks}")
        self.logger.info(f"inserting {block}") 
        self.blocks[block.index : ] = [] # OLD
        self.delete_blocks_from(block.index)
        self.unconfirmed_blocks[block] = 0 # OLD NOT REPLACED
        if block.index <= self.last_confirmed_block.index: # OLD
            self.last_confirmed_block = self.blocks[block.index - 1]
        self.blocks.append(block) # OLD
        self.insert_block(block, time()) # TODO CHECK ARRIVAL TIME

        return True

    # TODO: ideally i think it would be nice to deal with this
    # more elegantly using iterators and slices
    def merge(self, foreign_blocks: list[Block]) -> bool:
        self.logger.info(f"starting merge process with fork: {foreign_blocks}")
        idx = None
        first_foreign_block = foreign_blocks[0]
        for i, block in enumerate(self.blocks): # OLD
            # ignore genesis block
            if block.hash == 0:
                continue

            if block.hash == first_foreign_block.parent_hash:
                idx = i
                break

        id, idx_db = self.block_of_hash(first_foreign_block.parent_hash)

        if idx is None: # OLD
            self.logger.error(f"foreign subchain has no common ancestor with local chain")
            return False
        
        if idx_db is None:
            self.logger.error(f"foreign subchain has no common ancestor with local chain")
            return False


        self.logger.info(f"found common ancestor: {self.blocks[idx]}") # OLD
        self.logger.info(f"found common ancestor: {id}")
        # temporarily remove local fork from the chain
        # TODO from this point this function seems very optimizable
        original_local_subchain = self.blocks[idx + 1 : ] # OLD
        self.blocks[idx + 1 : ] = [] # OLD
        original_local_subchain_db = self.blocks_from_index(idx + 1)
        self.delete_blocks_from(idx+1)

        # try inserting the head of the fork
        if not self.insert(foreign_blocks.pop(0)):
            self.logger.info(f"merge failed: foreign chain is worse than local chain")
            self.blocks += original_local_subchain # OLD
            self.reintroduce_blocks(original_local_subchain_db)
            return False
        # if successful, try inserting all following blocks
        else:
            for block in foreign_blocks:
                if not self.insert(block):
                    break

        return True

    def _dump_state(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM localChains")
        for block in self.blocks: # OLD
            print(block) # OLD
        for block in cursor:
            print(block)
        self.connection.commit()
        cursor.close()

    def insert_block(self, block: Block, arrive_time: int):
        # ($indx$, $id$, $round$, $prev_hash$, $hash$, $node$, $mroot$, $tx$, $arrive_time$, fork, stable, subuser, $proof_hash$, numSuc, round_stable, VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        database_atributes = [block.index, block.hash, block.round, block.parent_hash, block.hash, block.owner_pubkey, "mroot", "tx", arrive_time, 0, 0, block.proof_hash, 0, 0] # TODO hash as id?
        cursor = self.connection.cursor()
        INSERT_QUERY = "INSERT INTO localChains (indx, id, round, prev_hash, hash, node, mroot, tx, arrive_time, fork, stable, subuser, proof_hash, numSuc, round_stable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(INSERT_QUERY, database_atributes)
        self.connection.commit()
        cursor.close()
    
    def block_in_blockchain(self, block: Block):
        FIND_BLOCK_QUERY = "SELECT * FROM tab2 WHERE hash = %s LIMIT 1"
        cursor = self.connection.cursor()
        cursor.execute(FIND_BLOCK_QUERY, [block.hash])
        block_in_blockchain = False
        for block in cursor:
            block_in_blockchain = True
        cursor.close()
        return block_in_blockchain
    
    def number_of_blocks(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM localChains")
        for i in cursor:
            count = i[0]
        cursor.close()
        return count

    def equal_parent_block(self, block: Block):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT hash FROM localChains WHERE indx = {block.index - 1}")
        for i in cursor:
            hash = i
        cursor.close()
        return hash == block.parent_hash

    def delete_blocks_from(self, index: int):
        cursor = self.connection.cursor()
        cursor.execute(f"DELETE FROM localChains WHERE indx >= {index}")
        self.connection.commit()
        cursor.close()

    def last_confirmed_block_id(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM localChains WHERE stable = 1 ORDER BY indx DESC LIMIT 1")
        for i in cursor:
            id = i
        cursor.close()
        return id
    
    def last_block_id(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM localChains ORDER BY indx DESC LIMIT 1")
        for i in cursor:
            id = i
        cursor.close()
        return id
    
    def oldest_unconfirmed_block(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT indx, id, numSuc, round, FROM localChains WHERE stable = 0 ORDER BY round ASC LIMIT 1")
        for i in cursor:
            indx, id, numSuc, round = i
        cursor.close()
        return indx, id, numSuc, round
    
    def confirm_block(self, id: int):
        cursor = self.connection.cursor()
        cursor.execute(f"UPDATE localChains SET stable = 1 WHERE id = {id}")
        self.connection.commit()
        cursor.close()

    def update_successfull_sortition(self, indx, winning_tickets):
        cursor = self.connection.cursor()
        cursor.execute(f"UPDATE localChains SET numSuc = numSuc + {winning_tickets} WHERE indx < {indx} AND stable = 0")
        self.connection.commit()
        cursor.close()

    def get_proof_hash_of_block(self, index):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT proof_hash FROM localChains WHERE indx = {index}")
        for i in cursor:
            proof_hash = i
        cursor.close()
        return proof_hash
    
    def get_round_of_block(self, index):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT round FROM localChains WHERE indx = {index}")
        for i in cursor:
            proof_hash = i
        cursor.close()
        return proof_hash
    
    def contains_in_db(self, block: Block): # TODO hash as id?
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT hash FROM localChains")
        for hash in cursor:
            if hash == block.hash:
                cursor.close()
                return True
        cursor.close()
        return False
    
    def block_of_hash(self, hash):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT id, indx, FROM localChains WHERE hash = {hash} ORDER BY indx ASC LIMIT 1")
        for i in cursor:
            id, indx = i
        cursor.close()
        return id, indx
    
    def block_of_hash(self, hash):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT id, indx, FROM localChains WHERE hash = {hash} ORDER BY indx ASC LIMIT 1")
        for i in cursor:
            id, indx = i
        cursor.close()
        return id, indx
    
    def blocks_from_index(self, index):
        cursor = self.connection.cursor()
        blocks_info = []
        cursor.execute(f"SELECT * FROM localChains WHERE indx >= {index} ORDER BY indx")
        for i in cursor:
            blocks_info.append(i)
        cursor.close()
        return blocks_info
    
    def reintroduce_blocks(self, list_of_blocks_data):
        # ($indx$, $id$, $round$, $prev_hash$, $hash$, $node$, $mroot$, $tx$, $arrive_time$, fork, stable, subuser, $proof_hash$, numSuc, round_stable, VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        cursor = self.connection.cursor()
        for block_data in list_of_blocks_data:
            INSERT_QUERY = "INSERT INTO localChains (indx, id, round, prev_hash, hash, node, mroot, tx, arrive_time, fork, stable, subuser, proof_hash, numSuc, round_stable) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(INSERT_QUERY, block_data)
        self.connection.commit()
        cursor.close()



# fixing index issue on update round and going to insert