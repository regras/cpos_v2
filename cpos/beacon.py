import argparse
import typing

from cpos.node import Node, NodeConfig
from cpos.protocol.messages import Hello, Message, MessageCode, PeerListRequest, PeerList
from cpos.p2p.network import Network

# class BeaconConfig:
#     def __init__(self, **kwargs):
#         self.port = kwargs.get("port", "8888")
#
#     def __str__(self):
#         return str(self.__dict__)
#
# class Beacon:
#     def __init__(self, config: BeaconConfig):
#         logger = logging.getLogger(__name__)
#         handler = logging.StreamHandler()
#         formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__}: %(message)s")
#         logger.setLevel(logging.DEBUG)
#         handler.setFormatter(formatter)
#         logger.addHandler(handler)
#         self.logger = logger
#
#         self.config = config
#
#         self.context = zmq.Context()
#         self.socket: zmq.Socket = self.context.socket(zmq.ROUTER)
#         self.socket.setsockopt(zmq.IDENTITY, b"beacon")
#         self.socket.bind(f"tcp://*:{self.config.port}")
#         self.logger.info(f"bound to tcp://*:{self.config.port}")
#
#         self.loop()
#
#     def loop(self):
#         while True:
#             try:
#                 peer_id, _, msg_raw = self.socket.recv_multipart()
#                 msg = Message.deserialize(msg_raw)
#                 self.logger.info(f"received: {msg}")
#                 match msg.code:
#                     case MessageCode.HELLO:
#                         pass
#                     case MessageCode.PEER_LIST_REQUEST:
#                         self.socket.send_multipart([peer_id, bytes(), PeerList(self.)])
#             except KeyboardInterrupt:
#                 break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="which port to bind the CPoS beacon to")
    parser.add_argument("--id", help="beacon ID", type=str, required=True)
    args = parser.parse_args()

    if args.id:
        args.id = bytes(args.id, 'ascii')

    config = NodeConfig(**vars(args))
    print(config)
    beacon = Node(config)

    while True:
        try:
            msg = beacon.read_message()
            if msg is None:
                continue
            match msg.code:
                case MessageCode.HELLO:
                    pass
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()

