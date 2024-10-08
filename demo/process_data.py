import os
from os.path import join
import pickle

import os


# NOT ADAPTED TO CURRENT CODE
# The blockchain atribute "blocks" was substituted by the blockchain database

def main():
    cwd = os.getcwd()
    log_dir = join(cwd, "demo/logs/")

    avg_throughput = 0
    total_message_count = 0
    total_message_bytes = 0
    total_blocks = 0
    total_confirmed_blocks = 0
    total = 0
    smallest_confirmation_delays = {}

    for filename in os.listdir(log_dir):
        if not filename.endswith(".data"):
            continue

        # plot local blockchain views and update statistics
        print(f"processing {filename}")
        with open(join(log_dir, filename), "rb") as file:
            bc, last_confirmed_block_info, confirmation_delays, message_count, message_bytes, blockchain_info, debug_info = pickle.load(file)
            throughput, block_count, confirmed_blocks = plot_bc(bc, last_confirmed_block_info, filename, blockchain_info)
            avg_throughput += throughput
            total_message_count += message_count
            total_message_bytes += message_bytes
            total_blocks += block_count
            total_confirmed_blocks += confirmed_blocks
            total += 1
            # block_delay has a format: [block_id, block_index, confirmation_delay (in rounds)]
            for block_delay in confirmation_delays:
                if not block_delay[1] in smallest_confirmation_delays or smallest_confirmation_delays[block_delay[1]] > block_delay[2]:
                    smallest_confirmation_delays[block_delay[1]] = block_delay[2]
        print(f"-------------------------------------\n")

    avg_throughput /= total
    average_confirmation_delay = sum(smallest_confirmation_delays.values()) / len(smallest_confirmation_delays)

    print(f"statistics: average throughput = {avg_throughput} blocks/min; average confirmation delay = {average_confirmation_delay}")
    print(f"total messages: {total_message_count} ({total_message_bytes / (1024 * 1024)} MiB)")
    print(f"total blocks = {total_blocks}; total confirmed blocks = {total_confirmed_blocks}")

def plot_bc(bc, last_confirmed_block_info, filename: str, blockchain_info: list):
    block_count = 0
    last_confirmed_block_index, last_confirmed_block_id, last_confirmed_block_round = last_confirmed_block_info
    round_time, last_confirmation_delay, current_round = blockchain_info
    confirmed_blocks = 0
    for block in bc:
        print(block)
        block_count += 1
        if block.hash == last_confirmed_block_id:
            confirmed_blocks = block_count
            print("=== [UNCONFIRMED BLOCKS] ===")

    # confirmed blocks per minute
    throughput = last_confirmed_block_index * 60 / (round_time * 30)

    return throughput, len(bc), confirmed_blocks

if __name__ == "__main__":
    main()
  