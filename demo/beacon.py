import argparse
import signal

from cpos.p2p.discovery.beacon import Beacon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="which port to bind the CPoS beacon to", type=int, required=True)
    args = parser.parse_args()

    beacon = Beacon(port=args.port)

    def sighandler(*args):
        print(f"Received SIGTERM! Halting node...")
        exit(1)

    signal.signal(signal.SIGINT, sighandler)
    signal.signal(signal.SIGTERM, sighandler)

    try:
        beacon.start()
    except KeyboardInterrupt:
        print("exiting...")

if __name__ == "__main__":
    main()

