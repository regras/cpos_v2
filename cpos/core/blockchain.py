from cpos.core.block import Block, GenesisBlock
from cpos.core.sortition import run_sortition
from time import time
from typing import Optional
import logging
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

class BlockChainParameters:
    def __init__(self, round_time: float, tolerance: int, tau: int, total_stake=10):
        self.round_time = round_time
        self.tolerance = tolerance
        self.tau = tau
        self.total_stake = total_stake
        pass

class BlockChain:
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

        if genesis is not None:
            self.genesis = genesis
        else:
            self.genesis = GenesisBlock()
        
        self.blocks.append(self.genesis)

        self.current_round = 0
        self.update_round()

    def update_round(self):
        current_time = time()
        genesis_time = self.genesis.timestamp
        delta_t = current_time - genesis_time
        self.current_round = int(delta_t / self.parameters.round_time)

    def _log_failed_verification(self, block: Block, reason: str):
        self.logger.debug(f"failed to verify block {block.hash.hex()} ({reason})")

    # TODO: these two are stubs, we need to implement an actual search
    # through the blockchain transactions later
    def lookup_node_stake(self, node_id: bytes) -> int:
        return 1
    def lookup_total_stake(self) -> int:
        return self.parameters.total_stake

    def validate_block(self, block: Block) -> bool:
        pubkey = None
        try:
            pubkey = Ed25519PublicKey.from_public_bytes(block.owner_pubkey)
        except ValueError:
            self._log_failed_verification(block, "bad pubkey")
            return False
        
        try:
            pubkey.verify(block.signed_node_hash, block.node_hash)
        except InvalidSignature:
            self._log_failed_verification(block, "bad node_hash signature")
            return False

        stake = self.lookup_node_stake(block.owner_pubkey)
        total_stake = self.lookup_total_stake()
        success_probability = self.parameters.tau / total_stake
        winning_tickets = run_sortition(block.signed_node_hash, stake, success_probability)
        self.logger.debug(f"ran sortition for block {block.hash.hex()[0:7]} (p = {success_probability}); result = {winning_tickets}")
        if winning_tickets == 0 or winning_tickets < block.ticket_number:
            self._log_failed_verification(block, "sortition failed")
            return False
        
        return True

    def _log_failed_insertion(self, block: Block, reason: str):
        self.logger.info(f"discarding block {block.hash.hex()} ({reason})")

    def set_genesis_block(self, genesis: GenesisBlock) -> bool:
        if len(self.blocks) != 0:
            self.logger.error(f"refusing to insert new genesis block")
            return False

        self.blocks.append(genesis)
        return True

    def insert(self, block: Block) -> bool:
        if block.index == 0:
            self._log_failed_insertion(block, "new genesis block")
            return False 
        if block.index > len(self.blocks):
            self._log_failed_insertion(block, "gap in local chain")
            return False
        
        if not self.validate_block(block):
            self._log_failed_insertion(block, "validation failed")
            return False

        if len(self.blocks) > block.index and not block.proof_hash < self.blocks[block.index].proof_hash:
            self._log_failed_insertion(block, "smaller proof_hash")
            return False
    
        if self.blocks[block.index - 1].hash != block.parent_hash:
            self._log_failed_insertion(block, "parent mismatch")
            return False

        self.logger.info(f"inserting {block}") 
        self.blocks.append(block)

        return True

    # TODO: ideally i think it would be nice to deal with this
    # more elegantly using iterators and slices
    def merge(self, foreign_blocks: list[Block]) -> bool:
        self.logger.info(f"starting merge process with fork: {foreign_blocks}")
        idx = None
        first_foreign_block = foreign_blocks[0]
        for i, block in enumerate(self.blocks):
            if block.hash == first_foreign_block.parent_hash:
                idx = i
                break

        if idx is None:
            self.logger.error(f"foreign subchain has no common ancestor with local chain")
            return False


        self.logger.info(f"found common ancestor: {self.blocks[idx]}")
        # temporarily remove local fork from the chain
        original_local_subchain = self.blocks[idx + 1 : ]
        self.blocks[idx + 1 : ] = []

        # try inserting the head of the fork
        if not self.insert(foreign_blocks.pop(0)):
            self.logger.info(f"merge failed: foreign chain is worse than local chain")
            self.blocks += original_local_subchain
            return False
        # if successful, try inserting all following blocks
        else:
            for block in foreign_blocks:
                if not self.insert(block):
                    break

        return True


    def _dump_state(self):
        for block in self.blocks:
            print(block)
