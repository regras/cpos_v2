from cpos.p2p.server import Server
from cpos.p2p.client import Client

def NodeConfig():
    def __init__(self, **kwargs):
        # various node configs
        pass
def Node():
    def __init__(self, node_id, config):
        self.id = node_id
        self.server = Server()
        self.client = Client()
