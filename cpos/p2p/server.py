import logging
import socket
import queue
import threading

class Server:
    def __init__(self, port=8888):
        # configure logging stuff
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(f"[%(asctime)s][%(levelname)s] {__name__} %(message)s")
        logger.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        # open TCP socket
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer = queue.Queue() # stores incoming raw messages

        self.logger.info(f"Setting up listener on port {port}")
        # TODO: investigate the implications of passing '' as the address
        self.listener.bind(('', port))
        listen_thread = threading.Thread(target=self.listen, args=())
        listen_thread.start()

    def listen(self):
        self.logger.debug(f"Server listening")
        listener = self.listener
        while True:
            listener.listen()
            connection, addr = listener.accept()
            self.logger.debug(f"Received connection request from {addr}")
            connection_thread = threading.Thread(target=self.handle_connection,
                                                 args=(connection, addr))
            connection_thread.start()

    def handle_connection(self, connection, addr):
        with connection:
            self.logger.debug(f"Accepting incoming connection from {addr}")
            while True:
                # TODO: we definitely need a better way to do this
                data = connection.recv(4096)
                self.buffer.put(data)
                if not data:
                    self.logger.info(f"Received message from {addr}: {data}")
                data = None
                break





