import os
from os.path import join
import pickle
import graphviz

from cpos.core.blockchain import BlockChain

# NOT ADAPTED TO CURRENT CODE
# The blockchain atribute "blocks" was substituted by the blockchain database

def main():
    cwd = os.getcwd()
    log_dir = join(cwd, "demo/logs")

    avg_throughput = 0
    avg_confirmation_delay = 0
    total_message_count = 0
    total_message_bytes = 0
    total = 0

    for filename in os.listdir(log_dir):
        if not filename.endswith(".data"):
            continue

        # plot local blockchain views and update statistics
        print(f"processing {filename}")
        with open(join(log_dir, filename), "rb") as file:
            bc, message_count, message_bytes = pickle.load(file)
            throughput, confirmation_delay = plot_bc(bc, filename)
            avg_throughput += throughput
            avg_confirmation_delay += confirmation_delay
            total_message_count += message_count
            total_message_bytes += message_bytes
            total += 1
        print(f"-------------------------------------\n")

    avg_throughput /= total
    avg_confirmation_delay /= total

    print(f"statistics: average throughput = {avg_throughput} blocks/min; average confirmation delay = {avg_confirmation_delay}s")
    print(f"total messages: {total_message_count} ({total_message_bytes / (1024 * 1024)} MiB)")

def plot_bc(bc: BlockChain, filename: str):
    dot = graphviz.Graph(filename)
    dot.format = "png"
    for block in bc.blocks:
        print(block)
        if block == bc.last_confirmed_block:
            print("=== [UNCONFIRMED BLOCKS] ===")
        dot.node(f"{block.index}", label=f"<<TABLE> <TR> <TD> hash: {block.hash.hex()[0:8]} </TD> </TR>  <TR> <TD> parent: {block.parent_hash.hex()[0:8]} </TD> </TR> <TR> <TD> owner: [{block.owner_pubkey.hex()[0:8]}] </TD> </TR> </TABLE>>")

    # confirmed blocks per minute
    throughput = bc.last_confirmed_block.index * 60 / (bc.parameters.round_time * bc.current_round)
    # block confirmation time
    confirmation_delay = bc.last_confirmation_delay * bc.parameters.round_time

    for i in range(0, len(bc.blocks) - 1):
        dot.edge(f"{i}", f"{i+1}")

    dot.render(directory="demo/logs")

    return throughput, confirmation_delay 

if __name__ == "__main__":
    main()
