from cpos.p2p.server import Server
from cpos.p2p.client import PeerConnection
import threading
import time

def main():
    server = Server()
    client = PeerConnection("127.0.0.1", 8888)


if __name__ == "__main__":
    main()
