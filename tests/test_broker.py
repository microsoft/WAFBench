from ftw_compatible_tool import broker


def receive_func(check_func, arg):
    assert(check_func(arg))


def test_subscribe():
    brk = broker.Broker()
    brk.subscribe("test_title", receive_func)
    try:
        brk.subscribe("test_title", 0)
        assert(False)
    except ValueError:
        assert(True)


def test_normal():
    brk = broker.Broker()
    brk.subscribe("test_title", receive_func)
    brk.publish("test_title", lambda x : x, True)
    brk.publish("empty_title", lambda x : x, False)
    

def test_multiple_subscribe():
    # only get a message although multiple subscribe 
    brk = broker.Broker()
    brk.subscribe("test_title", receive_func)
    brk.subscribe("test_title", receive_func)
    brk.subscribe("test_title", receive_func)
    brk.subscribe("test_title", receive_func)
    triggle_time = [0]
    def inc(x):
        triggle_time[0] += 1
        return True
    brk.publish("test_title", inc, 1)
    assert(triggle_time[0] == 1)


def test_strict_subscribe():
    brk = broker.Broker()
    brk.subscribe("strict_title", receive_func, {"arg":str})
    brk.publish("strict_title", lambda x : x, "OK")
    brk.publish("strict_title", lambda x : x, arg = "OK")
    try:
        brk.publish("strict_title", lambda x : x, arg = 0)
        assert(False)
    except ValueError:
        assert(True)

