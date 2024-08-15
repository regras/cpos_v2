from time import time
from typing import Optional
import logging
import random
import os
import pickle
import random 

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.core.block import Block, GenesisBlock
from cpos.core.blockchain import BlockChain, BlockChainParameters
from cpos.core.transactions import TransactionList, MockTransactionList
from cpos.p2p.network import Network

from cpos.protocol.messages import BlockBroadcast, Hello, Message, ResyncRequest, ResyncResponse, PeerForgetRequest

from cpos.p2p.peer import Peer


class NodeConfig:
    def __init__(self, **kwargs):
        self.port: int = kwargs.get("port", 8888)
        self.privkey: Optional[bytes] = kwargs.get("privkey", None)
        self.id: Optional[bytes] = kwargs.get("id", None)
        self.peerlist: Optional[list[Peer]] = kwargs.get("peerlist", None)
        self.beacon_ip: Optional[str] = kwargs.get("beacon_ip", None)
        self.beacon_port: Optional[int] = kwargs.get("beacon_port", None)
        self.genesis_timestamp: Optional[int] = kwargs.get("genesis_timestamp", None)
        self.total_rounds: Optional[int] = kwargs.get("total_rounds", None)

    def __str__(self):
        return str(self.__dict__)

class State:
    LISTENING = 0x01,
    RESYNCING = 0x02,

class Node:
    def __init__(self, config: NodeConfig):
        self.config = config

        use_mock_transactions = os.environ.get("MOCK_TRANSACTIONS", "false")
        use_mock_transactions = use_mock_transactions in ("true")
        self.use_mock_transactions = use_mock_transactions

        broadcast_created_block = os.environ.get("BROADCAST_CREATED_BLOCK", "true")
        self.broadcast_created_block = broadcast_created_block in ("true")

        broadcast_received_block = os.environ.get("BROADCAST_RECEIVED_BLOCK", "true")
        self.broadcast_received_block = broadcast_received_block in ("true")

        self.maximum_num_peers = int(os.environ.get("MAXIMUM_NUM_PEERS", "8"))
        self.minimum_num_peers = int(os.environ.get("MINIMUM_NUM_PEERS", "4"))

        if self.config.privkey is not None:
            self.privkey = Ed25519PrivateKey.from_private_bytes(self.config.privkey)
        else:
            self.privkey = Ed25519PrivateKey.generate()

        self.pubkey = self.privkey.public_key()
        if self.config.id is not None:
            self.id: bytes = self.config.id
        else:
            self.id: bytes = self.pubkey.public_bytes_raw()

        logger = logging.getLogger(__name__ + self.id.hex())
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: [{self.id.hex()[0:8]}] %(message)s")
        logger.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        self._init_network()

        # this is an improvised hack for demo purposes, here we should
        # resync with other nodes in the network and only generate a
        # genesis block if there are no other peers
        genesis = None
        if self.config.genesis_timestamp is not None:
            genesis = GenesisBlock(timestamp=self.config.genesis_timestamp)
            self.logger.info(f"generating genesis block: {genesis}")

        # TODO: we need to be able to, at runtinme:
        # - request the blockchain parameters from other nodes
        # params = BlockChainParameters(round_time=5, tolerance=2, tau=10, total_stake=25)
        round_time = float(os.getenv("ROUND_TIME", 5))
        tolerance = int(os.getenv("TOLERANCE", 2))
        tau = int(os.getenv("TAU", 10))
        total_stake = int(os.getenv("TOTAL_STAKE", 25))

        params = BlockChainParameters(round_time=round_time, tolerance=tolerance, tau=tau, total_stake=total_stake)
        self.bc: BlockChain = BlockChain(params, genesis=genesis, node_id=self.id)
        self.state = State.LISTENING
        self.missed_blocks: list[tuple[Block, bytes]] = []
        self.received_resync_blocks: list[Block] = []
        
        self.message_count = 0
        self.total_message_bytes = 0
        
        self.should_halt: bool = False

    # TODO: make the log_dir configurable
    def dump_data(self, log_dir: str):
        cwd = os.getcwd()
        filepath = os.path.join(cwd, log_dir, f"node_{self.id.hex()[0:8]}.data")
        self.logger.warning(f"Dumping data to {filepath}...")
        try:
            with open(filepath, "wb") as file:
                blockchain_info = [self.bc.parameters.round_time, self.bc.last_confirmation_delay, self.bc.current_round]
                data = pickle.dumps((self.bc.last_n_blocks(self.bc.number_of_blocks()), self.bc.last_confirmed_block_info(), self.message_count, self.total_message_bytes, blockchain_info))
                file.write(data)
                file.flush()
                file.close()
        except Exception as e:
            self.logger.error(f"Failed to dump data: {e}")


    def _init_network(self):
        self.network = Network(self.id, self.config.port, self.config.beacon_ip, self.config.beacon_port)
        self.config.peerlist = self.network.get_peerlist_from_beacon()

        if self.config.peerlist is not None:
            for peer in self.config.peerlist:
                if peer.id == self.id:
                    continue
                self.network.connect(peer.ip, peer.port, peer.id)

    def send_message(self, dest_peer_id: bytes, msg: Message):
        if isinstance(msg, BlockBroadcast):
            self.logger.debug(f"broadcasting {msg}")
        else:
            self.logger.debug(f"sending {msg} to peer {dest_peer_id.hex()[0:8]}")
        return self.network.send(dest_peer_id, msg.serialize())

    def read_message(self) -> Optional[Message]:
        raw = self.network.read()
        if raw is None:
            return None
        return Message.deserialize(raw)

    def broadcast_message(self, msg: Message, invalid_peers: list):
        for peer in self.network.known_peers:
            if not peer in invalid_peers:
                self.send_message(peer, msg)

    def greet_peers(self):
        for peer_id in self.network.known_peers:
            msg = Hello(self.id, self.config.port)
            self.send_message(peer_id, msg)

    def sign_block(self, block: Block):
        block.signed_node_hash = self.privkey.sign(block.node_hash)
        block.update()

    # TODO: this should be moved to a BlockChainManager class
    # TODO: we should have clean interfaces for accessing/iterating
    #       through the BlockChain elements (__getitem__, etc.) instead
    #       of indexing manually like we're doing now
    def generate_block(self) -> Optional[Block]:
        stake = self.bc.lookup_node_stake(self.id)
        candidate: Optional[Block] = None
        for i in range(0, stake):
            if self.use_mock_transactions:
                tx = MockTransactionList()
            else:
                tx = TransactionList()

            block = Block(parent_hash=self.bc.get_last_block_hash(),
                          transactionlist=tx,
                          owner_pubkey=self.pubkey.public_bytes_raw(),
                          signed_node_hash=b"",
                          round=self.bc.current_round,
                          index=self.bc.number_of_blocks(),
                          ticket_number=i)
            self.sign_block(block)
            block.ticket_number = i

            if not self.bc.validate_block(block):
                continue

            self.logger.debug(f"block candidate: {block}")
            
            if candidate is None or block.proof_hash < candidate.proof_hash:
                candidate = block

        if candidate is not None:
            self.logger.info(f"successfully generated a block: {candidate}")
        return candidate

    def handle_new_block(self, block: Block, peer_id: bytes):
        round = self.bc.current_round
        tolerance = self.bc.parameters.tolerance
        if block.round not in range(round, round + tolerance + 1):
            self.logger.info(f"discarding block {block.hash.hex()[0:8]} (outside of tolerance range)")
            return False
        if block.owner_pubkey == self.pubkey.public_bytes_raw():
            self.logger.info(f"discarding block {block.hash.hex()[0:8]} (produced by itself)")
            return False
        self.logger.info(f"trying to insert {block}")
        if not self.bc.insert(block):
            if not self.bc.block_in_blockchain(block):
                self.missed_blocks.append((block, peer_id))
            #if block not in self.bc:
            #    self.missed_blocks.append((block, peer_id))
        else:
            own_id = self.id if not None else self.config.id
            if self.broadcast_received_block:
                self.broadcast_message(BlockBroadcast(block, own_id), [peer_id, block.owner_pubkey])

    def control_number_of_peers(self):
        if len(self.network.known_peers) < self.minimum_num_peers: 
            self.logger.info(f"Number of peers too low, asking more from beacon")
            additional_peerlist = self.network.get_additional_peers_from_beacon() # peers are randomly selected by beacon and come in a random order
            if additional_peerlist is not None:
                for peer in additional_peerlist: # TODO maybe limit number of peers added here?
                    if peer.id == self.id or peer.id in self.network.known_peers:
                        continue
                    self.network.connect(peer.ip, peer.port, peer.id)

        while len(self.network.known_peers) > self.maximum_num_peers:
            random_peer_id = random.sample(self.network.known_peers, 1)[0]
            self.logger.info(f" Too many peers: {len(self.network.known_peers)}, forgetting peer: {random_peer_id.hex()[0:8]}")
            self.send_message(random_peer_id, PeerForgetRequest(self.id))
            self.network.forget_peer(random_peer_id)

    def loop(self):
        round = self.bc.genesis.timestamp
        initial_round = self.bc.current_round
        while True:
            if self.config.total_rounds is not None and self.bc.current_round >= initial_round + self.config.total_rounds:
                self.should_halt = True

            if self.should_halt:
                self.logger.error("halted")
                break
            
            # if we detect a fork, resync with a node that sent a random missed block
            if self.state == State.LISTENING and self.bc.fork_detected and self.missed_blocks:
                stopResyncing = False
                while True:
                    if len(self.missed_blocks) == 0:
                        stopResyncing = True
                        break
                    missed: tuple[Block, bytes] = random.choice(self.missed_blocks)
                    self.missed_blocks.remove(missed)
                    # Start by asking for its last block
                    request_index = -1
                    if self.send_message(missed[1], ResyncRequest(self.id, request_index)):
                        break
                if stopResyncing:
                    continue
                self.state = State.RESYNCING
                self.logger.info("started resyncing")

            self.bc.update_round()
            # on round change:
            if round != self.bc.current_round:
                self.logger.debug(f"state: {self.state}")
                self.network.notify_beacon() #  Notifies beacon this node is still alive and connected to the network
                # TODO: make the log_dir configurable (and maybe
                # don't log every single round...)
                self.dump_data("demo/logs")
                round = self.bc.current_round
                new_block = self.generate_block()
                if new_block is not None and self.broadcast_created_block: # if dishonest node isnt going to broadcast block, it is also not going to insert in local blockchain
                    self.bc.insert(new_block)
                    own_id = self.id if not None else self.config.id
                    if self.broadcast_created_block:
                        self.broadcast_message(BlockBroadcast(new_block, own_id), [])

            # the 200ms timeout prevents us from busy-waiting
            raw = self.network.read(timeout=200)
            if raw is None:
                continue

            self.message_count += 1
            self.total_message_bytes += len(raw)

            msg = Message.deserialize(raw)
            self.logger.debug(f"new message: {msg}")

            if self.state == State.LISTENING:
                if isinstance(msg, BlockBroadcast):
                    self.handle_new_block(msg.block, msg.peer_id)    
                if isinstance(msg, ResyncRequest):
                    peer_id = msg.peer_id
                    # make sure we only send stuff after the genesis block
                    # If there are blocks available at this index, send it
                    if self.bc.number_of_blocks() > abs(msg.block_index):
                        block_to_send = self.bc.block_by_index(msg.block_index)
                        self.send_message(peer_id, ResyncResponse(block_to_send))
                    # Else, send None to signal there are no blocks that match the request
                    else:
                        self.send_message(peer_id, ResyncResponse(None))
                if isinstance(msg, PeerForgetRequest):
                    self.logger.info(f"Received forget request from: {msg.peer_id.hex()[0:8]}")
                    self.network.forget_peer(msg.peer_id)

            if self.state == State.RESYNCING:
                if isinstance(msg, ResyncResponse):
                    # Store the received blocks
                    self.received_resync_blocks.insert(0, msg.block_received)

                    # If the peer doesn't have useful blocks, ask to another random peer
                    if not msg.block_received:
                        self.received_resync_blocks = []
                        if self.missed_blocks:
                            missed: tuple[Block, bytes] = random.choice(self.missed_blocks)
                            self.missed_blocks.remove(missed)
                            request_index = -1
                            self.send_message(missed[1], ResyncRequest(self.id, request_index))
                        else:
                            self.state = State.LISTENING
                            self.received_resync_blocks = []
                            self.bc.fork_detected = False
                            self.logger.info("resync finished unsuccessfully!")

                    # If the resync is successful, finish the resync
                    elif self.bc.merge(self.received_resync_blocks):
                        self.state = State.LISTENING
                        self.received_resync_blocks = []
                        self.bc.fork_detected = False
                        self.missed_blocks = []
                        self.logger.info("resync completed!")

                    # If it is needed to request for more blocks
                    else:
                        request_index -= 1
                        self.send_message(missed[1], ResyncRequest(self.id, request_index))
                          
                # we need to reply to ResyncRequest in order to avoid a
                # distributed deadlock
                if isinstance(msg, ResyncRequest):
                    peer_id = msg.peer_id
                    # make sure we only send stuff after the genesis block
                    # If there are blocks available at this index, send it
                    if self.bc.number_of_blocks() > abs(msg.block_index):
                        block_to_send = self.bc.block_by_index(msg.block_index)
                        self.send_message(peer_id, ResyncResponse(block_to_send))
                    # Else, send None to signal there are no blocks that match the request
                    else:
                        self.send_message(peer_id, ResyncResponse(None))

            self.control_number_of_peers()

    def start(self):
        self.should_halt = False
        self.logger.debug(f"peerlist: {sorted([i.hex()[0:8] for i in self.network.known_peers])}")
        self.greet_peers()
        self.loop()

    def halt(self):
        self.logger.error(f"trying to halt...")
        self.should_halt = True

    def __str__(self):
        return f"Node(id={self.id.hex()[0:8]})"