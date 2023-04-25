from cpos.protocol.message import Message, MessageCode
import logging

class RPC:
    def __init__(self):
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        # stores the message handlers (functions that are
        # called upon receiving a message of a certain class)
        self.handlers = {}

    def execute(self, message: Message):
        code = message.code
        if code in self.handlers:
            handler = self.handlers.get(code)
        else:
            self.logger.warning(f"Unimplemented RPC for message with code: {code}, ignoring...")
