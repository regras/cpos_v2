from time import sleep
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cpos.node import Node, NodeConfig
import pytest
from cpos.p2p.peer import Peer

from cpos.protocol.messages import Hello

# TODO: this is not a very good unit test (too complicated)
#       and seems to fail randomly (although rarely); consider
#       skipping
def test_basic_greeting():
    ports: list[int] = [8892, 8893, 8894, 8895]
    privkeys: list[Ed25519PrivateKey] = []
    peers = []
    nodes: list[Node] = []
    for port in ports:
        privkey = Ed25519PrivateKey.generate()
        pubkey = privkey.public_key().public_bytes_raw()
        privkeys.append(privkey)
        ip = "localhost"
        peers.append(Peer(ip, port, pubkey))

    for (privkey, port)  in zip(privkeys, ports):
        config = NodeConfig(port=port, privkey=privkey.private_bytes_raw(), peerlist=peers)
        node = Node(config)
        nodes.append(node)

    sleep(1)

    for node in nodes:
        node.greet_peers()

    sleep(1)

    for node in nodes:
        print("-------------")
        print(f"node: {node}")
        p = ports.copy()
        # we can't greet ourselves (zmq discards messages
        # sent to self)
        p.remove(node.config.port)
        while True:
            msg_raw = node.network.read(timeout=1000)
            if msg_raw is None:
                break
            msg = Hello.deserialize(msg_raw)
            print(msg)
            p.remove(int(msg.peer_port))
        # check that we received greetings from all peers
        assert len(p) == 0

def main():
    test_basic_greeting()

if __name__ == "__main__":
    main()
