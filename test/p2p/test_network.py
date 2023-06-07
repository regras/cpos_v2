from time import sleep
from cpos.p2p.network import Network
from cpos.protocol.messages import Hello

def test_basic_connectivity():
    a = Network(b"a", 8888)
    b = Network(b"b", 8889)
    a.connect("localhost", b.port, b.id)
    sleep(1)
    sent_msg = b"hello"
    a.send(b.id, sent_msg)
    recv_msg = b.read(timeout=200)
    assert recv_msg == sent_msg

def test_send_huge_payload():
    a = Network(b"a", 8888)
    b = Network(b"b", 8889)
    a.connect("localhost", b.port, b.id)
    sleep(1)
    # send 10MB of data
    sent_msg = bytes([0xFF]*10*1024*1024)
    a.send(b.id, sent_msg)
    recv_msg = b.read(timeout=1000)
    assert recv_msg == sent_msg

def test_basic_messaging():
    a = Network(b"a", 8888)
    b = Network(b"b", 8999)
    a.connect("localhost", b.port, b.id)
    sleep(1)
    sent_msg = Hello(a.id, a.port) 
    a.send(b.id, sent_msg.serialize())
    recv_raw = b.read(1000)
    assert recv_raw is not None
    recv_msg = Hello.deserialize(recv_raw)
    assert recv_msg.peer_id == sent_msg.peer_id
    assert recv_msg.peer_port == sent_msg.peer_port

def main():
    test_basic_connectivity()

if __name__ == "__main__":
    main()
