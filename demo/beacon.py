import argparse

from cpos.p2p.discovery.beacon import Beacon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="which port to bind the CPoS beacon to", type=int, required=True)
    args = parser.parse_args()

    beacon = Beacon(port=args.port)

    try:
        beacon.start()
    except KeyboardInterrupt:
        print("exiting...")

if __name__ == "__main__":
    main()

