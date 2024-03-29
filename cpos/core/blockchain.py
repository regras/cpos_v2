from cpos.core.block import Block, GenesisBlock
from cpos.core.sortition import fork_threshold, run_sortition, confirmation_threshold
from time import time
from typing import Optional
from collections import OrderedDict
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
    # TODO: make this faster? shouldn't be an issue once we
    #       implement SQL database support
    def __contains__(self, block: Block):
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
        if self.last_confirmed_block == self.blocks[-1]:
            return

        # oldest unconfirmed block
        oldest = self.blocks[self.last_confirmed_block.index + 1]
        delta_r = round - oldest.round

        if delta_r > 0 and oldest.index > 0:
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
        if len(self.blocks) != 0:
            self.logger.error(f"refusing to insert new genesis block")
            return False

        self.blocks.append(genesis)
        return True

    # try to insert a block at the end of the chain
    def insert(self, block: Block) -> bool:
        if block in self:
            self._log_failed_insertion(block, "already in local chain")
        if block.index == 0:
            self._log_failed_insertion(block, "new genesis block")
            return False 
        if block.index > len(self.blocks):
            self._log_failed_insertion(block, "gap in local chain")
            return False
    
        if self.blocks[block.index - 1].hash != block.parent_hash:
            self._log_failed_insertion(block, "parent mismatch")
            return False

        winning_tickets = self.validate_block(block)
        if not winning_tickets:
            self._log_failed_insertion(block, "validation failed")
            return False
        else:
            # update the successful sortition statistics
            preceding_blocks = self.blocks[0 : block.index]
            for b in preceding_blocks:
                if b in self.unconfirmed_blocks:
                    self.unconfirmed_blocks[b] += winning_tickets

        # in case there is already a block present at block.index
        if len(self.blocks) > block.index:
            if block.proof_hash <= self.blocks[block.index].proof_hash:
                self._log_failed_insertion(block, "smaller proof_hash")
                return False

        # reject block if it was added in the same round as the parent
        parent_idx = block.index - 1
        if block.round <= self.blocks[parent_idx].round:
            self._log_failed_insertion(block, "same round as parent")
            return False

        # self.logger.info(f"s: {self.unconfirmed_blocks}")
        self.logger.info(f"inserting {block}") 
        self.blocks[block.index : ] = []
        self.unconfirmed_blocks[block] = 0
        if block.index <= self.last_confirmed_block.index:
            self.last_confirmed_block = self.blocks[block.index - 1]
        self.blocks.append(block)

        return True

    # TODO: ideally i think it would be nice to deal with this
    # more elegantly using iterators and slices
    def merge(self, foreign_blocks: list[Block]) -> bool:
        self.logger.info(f"starting merge process with fork: {foreign_blocks}")
        idx = None
        first_foreign_block = foreign_blocks[0]
        for i, block in enumerate(self.blocks):
            # ignore genesis block
            if block.hash == 0:
                continue

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
