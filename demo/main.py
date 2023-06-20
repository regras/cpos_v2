import os
from os.path import join
from time import sleep
import argparse
import pickle
import signal


from cpos.node import Node, NodeConfig
from cpos.protocol.messages import Hello 


def main():
    parser = argparse.ArgumentParser()
    node_config = parser.add_argument_group("node_config")
    node_config.add_argument("-p", "--port", help="which port to bind the CPoS node to", type=int, required=True)
    node_config.add_argument("-k", "--key", help="the node's private key (in hex)", type=str)
    # node_config.add_argument("--peerlist", help="a list of peers in the network", nargs="+", type=tuple)
    node_config.add_argument("--genesis-timestamp", type=int, required=True)
    node_config.add_argument("--beacon-ip", help="the IP address of the network beacon", required=True, type=str)
    node_config.add_argument("--beacon-port", help="the port of the network beacon", required=True, type=int)
    args = parser.parse_args()
    print(vars(args))
    config = NodeConfig(**vars(args))
    print(config)
    node = Node(config)

    def ensure_log_dir():
        cwd = os.getcwd()
        log_dir = join(cwd, "demo/logs")
        if not os.path.exists(log_dir):
            print(f"creating log dir at {log_dir}")
            os.mkdir(log_dir)

    def dump_data():
        cwd = os.getcwd()
        log_dir = join(cwd, "demo/logs")
        with open(f"demo/logs/node_{node.id.hex()[0:8]}.data", "wb") as file:
            data = pickle.dump(node.bc, file)

    def sighandler(*args):
        print(f"Received SIGTERM! Halting node...")
        node.halt()

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    # ensure_log_dir()
    try:
        node.greet_peers()
        node.start()
    except KeyboardInterrupt:
        node.halt()
        pass

    print("exiting...")
    dump_data()

if __name__ == "__main__":
    main()

