from time import sleep
from cpos.node import Node, NodeConfig
from cpos.protocol.messages import Hello 
import argparse

def main():
    parser = argparse.ArgumentParser()
    node_config = parser.add_argument_group("node_config")
    node_config.add_argument("-p", "--port", help="which port to bind the CPoS node to", required=True)
    node_config.add_argument("-k", "--key", help="the node's private key (in hex)", type=str)
    node_config.add_argument("--peerlist", help="a list of peers in the network", nargs="+", type=tuple)
    node_config.add_argument("--beacon-ip", help="the IP address of the network beacon", required=True, type=str)
    node_config.add_argument("--beacon-port", help="the port of the network beacon", required=True, type=str)
    args = parser.parse_args()
    print(vars(args))
    config = NodeConfig(**vars(args))
    print(config)
    node = Node(config)
    node.network.connect(node.config.beacon_ip, node.config.beacon_port, b"beacon")
    sleep(1)
    node.send_message(b"beacon", Hello(node.id, node.config.port))

if __name__ == "__main__":
    main()

