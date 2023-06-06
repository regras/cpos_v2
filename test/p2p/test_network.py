from time import sleep
from cpos.p2p.network import Network
from cpos.protocol.messages import Hello

def test_basic_connectivity():
    a = Network(b"a", 8888)
    b = Network(b"b", 8889)
    a.connect(b.id, "localhost", b.port)
    sleep(1)
    sent_msg = b"hello"
    a.send(b.id, sent_msg)
    recv_msg = b.read()
    assert recv_msg == sent_msg

def test_send_huge_payload():
    a = Network(b"a", 8888)
    b = Network(b"b", 8889)
    a.connect(b.id, "localhost", b.port)
    sleep(1)
    # send 10MB of data
    sent_msg = bytes([0xFF]*10*1024*1024)
    a.send(b.id, sent_msg)
    recv_msg = b.read()
    assert recv_msg == sent_msg

def test_basic_messaging():
    a = Network(b"a", 8888)
    b = Network(b"b", 8999)
    a.connect(b.id, "localhost", b.port)
    sleep(1)
    sent_msg = Hello(a.id, a.port) 
    a.send(b.id, sent_msg.serialize())
    recv_msg = Hello.deserialize(b.read())
    assert recv_msg.peer_id == sent_msg.peer_id
    assert recv_msg.peer_port == sent_msg.peer_port

def main():
    test_basic_messaging()

if __name__ == "__main__":
    main()
