from cpos.net.channel import Channel, NetInfo

def test_channel_initialization():
    net_info = NetInfo("tcp", "192.168.0.1", 8000)
    channel = Channel(net_info)
    assert False
