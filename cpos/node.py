from time import time
from typing import Optional
import logging
import random
import os
import pickle

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.core.block import Block, GenesisBlock
from cpos.core.blockchain import BlockChain, BlockChainParameters
from cpos.core.transactions import TransactionList, MockTransactionList
from cpos.p2p.network import Network

from cpos.protocol.messages import BlockBroadcast, Hello, Message, ResyncRequest, ResyncResponse

from cpos.p2p.discovery.client import Client as DiscoveryClient
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

        self._contact_beacon()

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
        self.bc: BlockChain = BlockChain(params, genesis=genesis)
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
        self.logger.warning(f"Dumping data to {filepath}...");
        try:
            with open(filepath, "wb") as file:
                data = pickle.dumps((self.bc, self.message_count, self.total_message_bytes))
                file.write(data)
                file.flush()
                file.close()
        except Exception as e:
            self.logger.error(f"Failed to dump data: {e}")

    # TODO: this should probably be moved into the cpos.p2p.network
    def _contact_beacon(self):
        beacon_ip = self.config.beacon_ip
        beacon_port = self.config.beacon_port
        port = self.config.port
        id = self.id

        if beacon_ip is None or beacon_port is None:
            self.logger.error(f"missing beacon network info!")
            return
        
        client = DiscoveryClient(beacon_ip, beacon_port, port, id)
        peerlist = client.get_peerlist()
        if peerlist is not None:
            self.config.peerlist = peerlist


    def _init_network(self):
        self.network = Network(self.id, self.config.port)

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
        self.network.send(dest_peer_id, msg.serialize())

    def read_message(self) -> Optional[Message]:
        raw = self.network.read()
        if raw is None:
            return None
        return Message.deserialize(raw)

    def broadcast_message(self, msg: Message):
        for peer in self.network.known_peers:
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

            block = Block(parent_hash=self.bc.blocks[-1].hash,
                          transactions=tx,
                          owner_pubkey=self.pubkey.public_bytes_raw(),
                          signed_node_hash=b"",
                          round=self.bc.current_round,
                          index=len(self.bc.blocks),
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
        self.logger.info(f"trying to insert {block}")
        if not self.bc.insert(block):
            self.missed_blocks.append((block, peer_id))
        else:
            own_id = self.id if not None else self.config.id
            self.broadcast_message(BlockBroadcast(block, own_id))

    def loop(self):
        round = self.bc.genesis.timestamp
        while True:
            if self.config.total_rounds is not None and self.bc.current_round >= self.config.total_rounds:
                self.should_halt = True

            if self.should_halt:
                self.logger.error("halted")
                break
            
            # if we detect a fork, resync with a node that sent a random missed block
            if self.state == State.LISTENING and self.bc.fork_detected and self.missed_blocks:
                missed: tuple[Block, bytes] = random.choice(self.missed_blocks)
                self.missed_blocks.remove(missed)
                # Start by asking for its last block
                request_index = -1
                self.send_message(missed[1], ResyncRequest(self.id, request_index))
                self.state = State.RESYNCING
                self.logger.info("started resyncing")

            self.bc.update_round()
            # on round change:
            if round != self.bc.current_round:
                self.logger.debug(f"state: {self.state}")
                # TODO: make the log_dir configurable (and maybe
                # don't log every single round...)
                self.dump_data("demo/logs")
                round = self.bc.current_round
                new_block = self.generate_block()
                if new_block is not None:
                    self.bc.insert(new_block)
                    own_id = self.id if not None else self.config.id
                    self.broadcast_message(BlockBroadcast(new_block, own_id))

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
                    if len(self.bc.blocks) > abs(msg.block_index):
                        block_to_send = self.bc.blocks[msg.block_index]
                        self.send_message(peer_id, ResyncResponse(block_to_send))
                    # Else, send None to signal there are no blocks that match the request
                    else:
                        self.send_message(peer_id, ResyncResponse(None))

            if self.state == State.RESYNCING:
                if isinstance(msg, ResyncResponse):
                    # Store the received blocks
                    self.received_resync_blocks.insert(0, msg.block_received)

                    # If the peer doesn't have useful blocks, ask to another random peer
                    if not msg.block_received:
                        self.received_resync_blocks = []
                        missed: tuple[Block, bytes] = random.choice(self.missed_blocks)
                        self.missed_blocks.remove(missed)
                        request_index = -1
                        self.send_message(missed[1], ResyncRequest(self.id, request_index))

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
                    if len(self.bc.blocks) > abs(msg.block_index):
                        block_to_send = self.bc.blocks[msg.block_index]
                        self.send_message(peer_id, ResyncResponse(block_to_send))
                    # Else, send None to signal there are no blocks that match the request
                    else:
                        self.send_message(peer_id, ResyncResponse(None))

    def start(self):
        self.should_halt = False
        self.logger.debug(f"peerlist: {self.network.known_peers}")
        self.greet_peers()
        self.loop()

    def halt(self):
        self.logger.error(f"trying to halt...")
        self.should_halt = True

    def __str__(self):
        return f"Node(id={self.id.hex()[0:8]})"


