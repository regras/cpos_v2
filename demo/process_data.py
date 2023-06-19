import os
from os.path import join
import pickle
import graphviz

from cpos.core.blockchain import BlockChain

def main():
    cwd = os.getcwd()
    log_dir = join(cwd, "demo/logs")
    for filename in os.listdir(log_dir):
        if not filename.endswith(".data"):
            continue
        with open(join(log_dir, filename), "rb") as file:
            bc: BlockChain = pickle.load(file)
            plot_bc(bc, filename)

def plot_bc(bc: BlockChain, filename: str):
    dot = graphviz.Graph(filename)
    dot.format = "png"
    for block in bc.blocks:
        dot.node(f"{block.index}", label=f"<<TABLE> <TR> <TD> hash: {block.hash.hex()[0:8]} </TD> </TR>  <TR> <TD> parent: {block.parent_hash.hex()[0:8]} </TD> </TR> <TR> <TD> owner: [{block.owner_pubkey.hex()[0:8]}] </TD> </TR> </TABLE>>")

    for i in range(0, len(bc.blocks) - 1):
        dot.edge(f"{i}", f"{i+1}")

    dot.render(directory="demo/logs")

if __name__ == "__main__":
    main()
