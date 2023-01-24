from cpos.protocol.messages import Hello

def test_hello_serialization():
    msg = Hello()
    print(msg.serialize())
    assert True
