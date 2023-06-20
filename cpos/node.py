from time import time
from typing import Optional
import logging

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.core.block import Block, GenesisBlock
from cpos.core.blockchain import BlockChain, BlockChainParameters
from cpos.core.transactions import TransactionList
from cpos.p2p.network import Network

from cpos.protocol.messages import BlockBroadcast, Hello, Message

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

    def __str__(self):
        return str(self.__dict__)

class State:
    LISTENING = 0x01,
    RESYNCING = 0x02,

class Node:
    def __init__(self, config: NodeConfig):
        self.config = config

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
        logger.setLevel(logging.DEBUG)
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
        # - request a copy of the blockchain (implement sync)
        params = BlockChainParameters(round_time=1, tolerance=2, tau=1, total_stake=10)
        self.bc: BlockChain = BlockChain(params, genesis=genesis)
        
        self.should_halt: bool = False

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

    def handle_new_block(self, block: Block):
        self.logger.info(f"trying to insert {block}")
        self.bc.insert(block)

    def loop(self):
        round = self.bc.genesis.timestamp
        while True:
            if self.should_halt:
                self.logger.error("halted")
                break

            self.bc.update_round()
            # on round change:
            if round != self.bc.current_round:
                round = self.bc.current_round
                new_block = self.generate_block()
                if new_block is not None:
                    self.bc.insert(new_block)
                    self.broadcast_message(BlockBroadcast(new_block))

            raw = self.network.read()
            if raw is None:
                continue
            msg = Message.deserialize(raw)
            self.logger.debug(f"new message: {msg}")

            if isinstance(msg, BlockBroadcast):
                self.handle_new_block(msg.block)    

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


