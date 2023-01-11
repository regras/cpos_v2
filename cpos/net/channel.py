import logging

class NetInfo:
    def __init__(self, protocol: str, ip: str, port: int):
        self.protocol = protocol
        self.ip = ip
        self.port = port

class Channel:
    def __init__(self, net_info: NetInfo):
        # configure logging stuff
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        self.logger = logger
        self.logger.info(f"Started channel on {net_info.protocol}://{net_info.ip}:{net_info.port}")
