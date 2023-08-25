import argparse
import signal
from time import sleep

from cpos.p2p.discovery.beacon import Beacon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="which port to bind the CPoS beacon to", type=int, required=True)
    args = parser.parse_args()

    beacon = Beacon(port=args.port, instant_reply=False)

    def sighandler(*args):
        print(f"Received SIGTERM! Halting node...")
        exit(1)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    try:
        beacon.start()
        sleep(10)
        beacon.halt()
        beacon.broadcast_random_peers(5)
    except KeyboardInterrupt:
        print("exiting...")

if __name__ == "__main__":
    main()

