import os
import uuid
import filecmp
import BaseHTTPServer
import threading
import functools

from ftw_compatible_tool import base
from ftw_compatible_tool import context
from ftw_compatible_tool import broker
from ftw_compatible_tool import database
from ftw_compatible_tool import traffic

import common

def warning_as_error(*args):
    raise ValueError(*args)


def test_commands_dispatch():
    class Trigger(object):
        def __init__(self):
            self.count = 0
        def expect(self, expected):
            self.expected = expected
        def __call__(self, target):
            assert(target == self.expected)
            self.count += 1
    ctx = context.Context(broker.Broker())
    ctx.broker.subscribe(broker.TOPICS.WARNING, warning_as_error)
    t = Trigger()
    conf = base.BaseConf(functions={
        "test_func1": t,
        "test_func2": t,
    })
    bs = base.Base(ctx, conf)
    t.expect(1)
    bs._command("test_func1", 1)
    t.expect(2)
    bs._command("test_func2", 2)
    assert(t.count == 2)


def test_load_and_gen_packets():
    class FixUUID(object):
        def __init__(self):
            self.number = 0
        def __call__(self):
            self.number += 1
            return uuid.UUID(int=self.number - 1)
    old_uuid1 = uuid.uuid1
    uuid.uuid1 = FixUUID()
    ctx = context.Context(broker.Broker(), traffic.Delimiter("magic"))
    ctx.broker.subscribe(broker.TOPICS.WARNING, warning_as_error)
    conf = base.BaseConf()
    bs = base.Base(ctx, conf)
    database.Sqlite3DB(ctx)
    packets_yaml = os.path.join(
        os.path.dirname(__file__), "data", "packets.yaml")
    bs._load_yaml_tests(packets_yaml)
    bs._gen_requests()
    packets_pkt = conf.pkt_path
    expect_pkt = os.path.join(
        os.path.dirname(__file__), "data", "packets.pkt")
    filecmp.cmp(packets_pkt, expect_pkt)
    uuid.uuid1 = old_uuid1


def test_start_experiment():
    counter = {
        "request" : 0,
    }
    def check_result(row, result):
        assert(functools.reduce(lambda x, y: x and y, result.values()))
        counter["request"] += 1
    with common.HTTPServerInstance():
        ctx = context.Context(broker.Broker(), traffic.Delimiter("magic"))
        ctx.broker.subscribe(broker.TOPICS.WARNING, warning_as_error)
        conf = base.BaseConf()
        bs = base.Base(ctx, conf)

        ctx.broker.subscribe(broker.TOPICS.CHECK_RESULT, check_result)

        traffic.RawRequestCollector(ctx)
        traffic.RawResponseCollector(ctx)
        traffic.RealTrafficCollector(ctx)
        database.Sqlite3DB(ctx)

        packets_yaml = os.path.join(
            os.path.dirname(__file__), "data", "packets.yaml")
        bs._load_yaml_tests(packets_yaml)
        bs._gen_requests()
        assert(bs._start_experiment("localhost:" + str(common._PORT)) == 0)
        bs._report_experiment()
        assert(counter["request"] == 2)

    
def test_import_log():
    class LogCheck(object):
        def __init__(self, expected_log):
            if os.path.exists(expected_log):
                with open(expected_log, "r") as fd:
                    self.expected_log = iter(fd.readlines())
            else:
                self.expected_log = iter([expected_log])
        def __call__(self, line):
            assert(line == next(self.expected_log))
        def finish(self):
            try:
                next(self.expected_log)
                return False
            except StopIteration:
                return True
    ctx = context.Context(broker.Broker())
    ctx.broker.subscribe(broker.TOPICS.WARNING, warning_as_error)
    conf = base.BaseConf()
    bs = base.Base(ctx, conf)

    lc = LogCheck("test log")
    ctx.broker.subscribe(broker.TOPICS.RAW_LOG, lc)
    bs._import_log("test log")
    ctx.broker.unsubscribe(broker.TOPICS.RAW_LOG, lc)
    assert(lc.finish())

    lc = LogCheck(__file__)
    ctx.broker.subscribe(broker.TOPICS.RAW_LOG, lc)
    bs._import_log(__file__)
    ctx.broker.unsubscribe(broker.TOPICS.RAW_LOG, lc)
    assert(lc.finish())


def test_result_report():
    class FakeQueryResult(object):
        def __init__(self, data):
            self.data = iter(data)
        def __iter__(self):
            for i in self.data:
                yield i
        def title(self):
            return (
                "traffic_id",
                "test_title",
                "output",
                "raw_request",
                "raw_response",
                "raw_log"
            )
    class ResultChecker(object):
        def __init__(self, brk, test_data, expected):
            self.test_data = iter(test_data)
            self.expected = iter(expected)
            brk.subscribe(broker.TOPICS.SQL_COMMAND, self.publish_data)
            brk.subscribe(broker.TOPICS.CHECK_RESULT, self.check)
        def publish_data(self, *args, **kwargs):
            if "callback" in kwargs:
                kwargs["callback"](FakeQueryResult(self.test_data))
        def check(self, row, result):
            assert(result == next(self.expected))
        def finish(self):
            try:
                next(self.expected)
                return False
            except StopIteration:
                return True
    ctx = context.Context(broker.Broker())
    # ctx.broker.subscribe(broker.TOPICS.WARNING, warning_as_error)
    conf = base.BaseConf()
    bs = base.Base(ctx, conf)

    test_data = (
        (
            (
                "", "", "", "", "", ""
            ),
            {}
        ),
        (
            (
                "1", "1", "{'status' : 403}", "", "HTTP1.1 403", ""
            ),
            {"status": True}
        ),
        (
            (
                "1", "1", "{'status' : 403}", "", "HTTP1.1 200", ""
            ),
            {"status": False}
        ),
        (
            (
                "1", "1", "{'status' : [200, 404]}", "", "HTTP1.1 200", ""
            ),
            {"status": True}
        ),
        (
            (
                "1", "1", "{'log_contains' : 'a\da'}", "", "", "abcde"
            ),
            {"log_contains": False}
        ), 
        (
            (
                "1", "1", "{'log_contains' : 'a\da'}", "", "", "ab[a1a]cde"
            ),
            {"log_contains": True}
        ), 
        (
            (
                "1", "1", "{'no_log_contains' : 'a\da'}", "", "", "ab[a1a]cde"
            ),
            {"no_log_contains": False}
        ), 
        (
            (
                "1", "1", "{'no_log_contains' : 'a\da'}", "", "", "abcdef"
            ),
            {"no_log_contains": True}
        ), 
        (
            (
                "1", "1", "{'response_contains' : 'a\da'}", "", "abcdef", ""
            ),
            {"response_contains": False}
        ), 
        (
            (
                "1", "1", "{'response_contains' : 'a\da'}", "", "ab[a1a]cde", ""
            ),
            {"response_contains": True}
        ), 
        (
            (
                "1", "1", "{'expect_error' : True}", "", "abcdef", ""
            ),
            {"expect_error": False}
        ), 
        (
            (
                "1", "1", "{'expect_error' : True}", "", "", ""
            ),
            {"expect_error": True}
        ), 
    )
    rc = ResultChecker(
        ctx.broker,
        [v[0] for v in test_data],
        [v[1] for v in test_data])
    bs._report_experiment()
    assert(rc.finish())

