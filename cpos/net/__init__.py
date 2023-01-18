import zmq
import logging

zmq_context = zmq.Context()
logging.getLogger(__name__).addHandler(logging.NullHandler())
