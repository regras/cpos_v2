import os
from os.path import join
import pickle
import graphviz

import os
print(os.getcwd())

from cpos.core.blockchain import BlockChain

# NOT ADAPTED TO CURRENT CODE
# The blockchain atribute "blocks" was substituted by the blockchain database

def main():
    cwd = os.getcwd()
    log_dir = join(cwd, "demo/logs/cpos_test_logs")

    avg_throughput = 0
    avg_confirmation_delay = 0
    total_message_count = 0
    total_message_bytes = 0
    total_blocks = 0
    total_confirmed_blocks = 0
    total = 0

    for filename in os.listdir(log_dir):
        if not filename.endswith(".data"):
            continue

        # plot local blockchain views and update statistics
        print(f"processing {filename}")
        with open(join(log_dir, filename), "rb") as file:
            bc, message_count, message_bytes = pickle.load(file)
            throughput, confirmation_delay, block_count, confirmed_blocks = plot_bc(bc, filename)
            avg_throughput += throughput
            avg_confirmation_delay += confirmation_delay
            total_message_count += message_count
            total_message_bytes += message_bytes
            total_blocks += block_count
            total_confirmed_blocks += confirmed_blocks
            total += 1
        print(f"-------------------------------------\n")

    avg_throughput /= total
    avg_confirmation_delay /= total

    print(f"statistics: average throughput = {avg_throughput} blocks/min; average confirmation delay = {avg_confirmation_delay}s")
    print(f"total messages: {total_message_count} ({total_message_bytes / (1024 * 1024)} MiB)")
    print(f"total blocks = {total_blocks}; total confirmed blocks = {total_confirmed_blocks}")

def plot_bc(bc: BlockChain, filename: str):
    block_count = 0
    dot = graphviz.Graph(filename)
    dot.format = "png"
    blocks = bc.last_n_blocks(bc.number_of_blocks())
    last_confirmed_block_index, last_confirmed_block_id, last_confirmed_block_round = bc.last_confirmed_block_info()
    for block in blocks:
        print(block)
        block_count += 1
        if block.hash.hex() == last_confirmed_block_id:
            confirmed_blocks = block_count
            print("=== [UNCONFIRMED BLOCKS] ===")
        dot.node(f"{block.index}", label=f"<<TABLE> <TR> <TD> hash: {block.hash.hex()[0:8]} </TD> </TR>  <TR> <TD> parent: {block.parent_hash.hex()[0:8]} </TD> </TR> <TR> <TD> owner: [{block.owner_pubkey.hex()[0:8]}] </TD> </TR> </TABLE>>")

    # confirmed blocks per minute
    throughput = last_confirmed_block_index * 60 / (bc.parameters.round_time * bc.current_round)
    # block confirmation time
    confirmation_delay = bc.last_confirmation_delay * bc.parameters.round_time

    for i in range(0, len(blocks) - 1):
        dot.edge(f"{i}", f"{i+1}")

    dot.render(directory="demo/logs")

    return throughput, confirmation_delay, len(blocks), confirmed_blocks

if __name__ == "__main__":
    main()
