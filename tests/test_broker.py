from ftw_compatible_tool import broker


def receive_func(check_func, arg):
    assert(check_func(arg))


class receive_class(object):
    def __call__(self, check_func, arg):
        assert(check_func(arg))


def test_subscribe():
    brk = broker.Broker()
    # normal subscribe
    brk.subscribe("test_title", receive_func)
    try:
        brk.subscribe("test_title", 0)
        assert(False)
    except ValueError as e:
        assert(str(e) == "subscriber<0> is not callable")

    # strict subscribe
    brk.subscribe("test_title2", lambda x: x, {"x": str})
    try:
        brk.subscribe("test_title", lambda x: x, {"x": str})
        assert(False)
    except ValueError as e:
        assert(
            str(e) ==
            "type limit<{'x': <type 'str'>}> is not compatible with previous<{}>")

    # callable object subscribe
    brk.subscribe("test_title", receive_class())


def test_publish():
    brk = broker.Broker()
    brk.subscribe("test_title", receive_func)
    brk.subscribe("test_title", receive_class())
    brk.publish("test_title", lambda x : x, True)
    brk.publish("empty_title", lambda x : x, False)

    # strict publish
    brk.subscribe("strict_title", receive_func, {"arg":str})
    brk.publish("strict_title", lambda x : x, "OK")
    brk.subscribe("strict_title", receive_class(), {"arg":str})
    brk.publish("strict_title", lambda x : x, "OK")
    brk.publish("strict_title", lambda x : x, arg = "OK")
    try:
        brk.publish("strict_title", lambda x : x, arg = 0)
        assert(False)
    except ValueError:
        assert(True)

   

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
    # unsubscribe
    brk.unsubscribe("test_title", receive_func)
    brk.publish("test_title", inc, 1)
    assert(triggle_time[0] == 1)


