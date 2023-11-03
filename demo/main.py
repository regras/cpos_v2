import os
from os.path import join
from time import sleep
import argparse
import pickle
import signal
import threading

from cpos.node import Node, NodeConfig
from cpos.protocol.messages import Hello
from demo.populate_mempool import populate_mempool

def main():
    parser = argparse.ArgumentParser()
    node_config = parser.add_argument_group("node_config")
    node_config.add_argument("-p", "--port", help="which port to bind the CPoS node to", type=int, required=True)
    node_config.add_argument("-k", "--key", help="the node's private key (in hex)", type=str)
    # node_config.add_argument("--peerlist", help="a list of peers in the network", nargs="+", type=tuple)
    node_config.add_argument("--genesis-timestamp", type=int, required=True)
    node_config.add_argument("--beacon-ip", help="the IP address of the network beacon", required=True, type=str)
    node_config.add_argument("--beacon-port", help="the port of the network beacon", required=True, type=int)
    node_config.add_argument("--total-rounds", help="total number of rounds before halting", required=False, type=int)
    args = parser.parse_args()
    print(vars(args))
    config = NodeConfig(**vars(args))
    print(config)
    node = Node(config)
    sleep(5)

    def sighandler(*args):
        node.logger.error(f"Received SIGTERM! Exiting...")
        exit(1)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    # Separate thread for mempool populator
    thread = threading.Thread(target=populate_mempool)
    thread.start()

    try:
        node.greet_peers()
        node.start()
    except KeyboardInterrupt:
        exit(1)


if __name__ == "__main__":
    main()

