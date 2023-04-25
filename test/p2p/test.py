from cpos.p2p.server import Server
from cpos.p2p.client import Client
from cpos.protocol.message import Hello
import threading
import time

def main():
    server = Server()
    for i in range(3):
        client = Client()
        client.register("test_peer", "192.168.0.1", 8888)
        client.connect("test_peer")
        msg = Hello("test_peer_1", 8888)
        client.send("test_peer", msg.serialize())
        time.sleep(3)

if __name__ == "__main__":
    main()
