#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" traffic
"""

from __future__ import print_function
import uuid
import re

import collector
import context
import broker
import sql

REQUEST_PATTERN = r"^writing request\((\d+) bytes\)\=\>\["
RESPONSE_PATTERN = r"^LOG\: http packet received\((\d+) bytes\)\:\n"
FINISH_PATTERN = r"^Finished \d+ requests"


class _RawPacketCollector(collector.SwitchCollector):
    def __init__(self, start_pattern, end_pattern, topic, ctx):
        super(_RawPacketCollector, self).__init__(start_pattern, end_pattern)
        self._topic = topic
        self._ctx = ctx
        self._ctx.broker.subscribe(broker.TOPICS.PYWB_OUTPUT, self)
        self._ctx.broker.subscribe(broker.TOPICS.RESET, self._reset)

    def __del__(self):
        self._ctx.broker.unsubscribe(broker.TOPICS.PYWB_OUTPUT, self)
        self._ctx.broker.unsubscribe(broker.TOPICS.RESET, self._reset)

    def _execute(self, collected_buffer, start_result, end_result):
        received_size = int(start_result.group(1))
        if len(collected_buffer) < received_size:
            self._ctx.broker.publish(
                broker.TOPICS.WARNING, "package lose message(%s)" %
                (received_size - len(collected_buffer), ))
            received_size = len(collected_buffer)
        package = collected_buffer[:received_size]
        self._ctx.broker.publish(self._topic, package)


class RawRequestCollector(_RawPacketCollector):
    def __init__(self, ctx):
        super(RawRequestCollector, self).__init__(
            REQUEST_PATTERN, r"(%s)|(%s)|(%s)" %
            (REQUEST_PATTERN, RESPONSE_PATTERN, FINISH_PATTERN),
            broker.TOPICS.RAW_REQUEST, ctx)


class RawResponseCollector(_RawPacketCollector):
    def __init__(self, ctx):
        super(RawResponseCollector, self).__init__(
            RESPONSE_PATTERN, r"(%s)|(%s)|(%s)" %
            (RESPONSE_PATTERN, REQUEST_PATTERN, FINISH_PATTERN),
            broker.TOPICS.RAW_RESPONSE, ctx)


class RealTrafficCollector(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._current_key = None
        self._request_buffer = ""
        self._response_buffer = ""
        self._state = collector.COLLECT_STATE.FINISH_COLLECT
        self._ctx.broker.subscribe(broker.TOPICS.RAW_REQUEST,
                                   self.collect_raw_request)
        self._ctx.broker.subscribe(broker.TOPICS.RAW_RESPONSE,
                                   self.collect_raw_response)
        self._ctx.broker.subscribe(broker.TOPICS.RESET, self._reset)

    def __del__(self):
        self._ctx.broker.unsubscribe(broker.TOPICS.RAW_REQUEST,
                                     self.collect_raw_request)
        self._ctx.broker.unsubscribe(broker.TOPICS.RAW_RESPONSE,
                                     self.collect_raw_response)
        self._ctx.broker.unsubscribe(broker.TOPICS.RESET, self._reset)

    def _publish(self):
        self._ctx.broker.publish(
            broker.TOPICS.SQL_QUERY,
            sql.SQL_INSERT_RAW_TRAFFIC,
            self._request_buffer,
            self._response_buffer,
            self._current_key,
        )
        self._ctx.broker.publish(
            broker.TOPICS.RAW_TRAFFIC,
            self._current_key,
            self._request_buffer,
            self._response_buffer,
        )

    def _reset(self):
        self._current_key = None
        self._request_buffer = ""
        self._response_buffer = ""
        self._state = collector.COLLECT_STATE.FINISH_COLLECT

    def collect_raw_request(self, raw_request):
        key = self._ctx.delimiter.get_delimiter_key(raw_request)
        if key:
            if self._current_key is None:
                self._current_key = key
            elif self._current_key == key:
                self._publish()
                self._current_key = None
                self._request_buffer = ""
                self._response_buffer = ""
            else:
                self._ctx.broker.publish(
                    broker.TOPICS.ERROR,
                    "Lose request %s" % (self._current_key))
                return
        else:
            self._request_buffer += raw_request

    def collect_raw_response(self, raw_response):
        if self._current_key is None:
            if self._state == collector.COLLECT_STATE.START_COLLECT:
                self._state = collector.COLLECT_STATE.FINISH_COLLECT
        # key was set
        elif self._state == collector.COLLECT_STATE.FINISH_COLLECT:
            self._state = collector.COLLECT_STATE.START_COLLECT
        elif self._state == collector.COLLECT_STATE.START_COLLECT:
            self._response_buffer += raw_response
        else:
            self._ctx.broker.publish(broker.TOPICS.ERROR,
                                     "Internal state error")
            return


class Delimiter(object):
    _MAGIC_PATTERN = r"{magic_string}-<{unique_key}>"

    _DELIMITER_PACKET_FORMAT = r'''
---
  meta:
    author: "Microsoft"
    enabled: true
    description: "Delimiter packet"
  tests:
    -
      test_title: {magic_pattern}
      stages:
        -
          stage:
            input:
              dest_addr: "127.0.0.1"
              port: 80
              uri: "/"
              headers:
                  User-Agent: "WAFBench"
                  Host: "{magic_pattern}"
                  Accept: "*/*"
            output:
                  log_contains: ""
    '''

    _DELIMITER_RULE_FORMAT = r'''
SecRule REQUEST_HEADERS:Host "{magic_pattern}" \
    "phase:5,\
    id:010203,\
    t:none,\
    block,\
    msg:'delimiter-%{{matched_var}}'"
    '''

    @staticmethod
    def _generate_magic_string():
        return "%s" % (uuid.uuid1().int, )

    def __init__(self, magic_string=None):
        if magic_string:
            self._magic_string = magic_string
        else:
            self._magic_string = Delimiter._generate_magic_string()
        pattern = Delimiter._MAGIC_PATTERN.format(
            **{
                "magic_string": self._magic_string,
                "unique_key": r"(\w*)",
            })
        self._magic_searcher = re.compile(pattern)

    def get_delimiter_rule(self):
        return Delimiter._DELIMITER_RULE_FORMAT.format(
            **{"magic_pattern": self._magic_searcher.pattern})

    def get_delimiter_key(self, line):
        result = self._magic_searcher.search(line)
        if result:
            return result.group(1)
        else:
            return None

    def get_delimiter_packet(self, key):
        yaml_string = Delimiter._DELIMITER_PACKET_FORMAT.format(
            **{
                "magic_pattern":
                Delimiter._MAGIC_PATTERN.format(
                    **{
                        "magic_string": self._magic_string,
                        "unique_key": str(key)
                    })
            })
        return yaml_string

    def get_delimiter_log(self):
        return "msg \"delimiter-%s\"" % (self._magic_searcher.pattern, )


if __name__ == "__main__":
    import testdata

    ctx = context.Context(
        broker.Broker(),
        delimiter=Delimiter("334787923864975794240893756898805143302"))
    request_collector = RawRequestCollector(ctx)
    response_collector = RawResponseCollector(ctx)
    traffic_collector = RealTrafficCollector(ctx)

    def PrintMessage(*args, **kwargs):
        print(repr(args))
        print(repr(kwargs))

    ctx.broker.subscribe(broker.TOPICS.SQL_QUERY, PrintMessage)

    for line in testdata.TEST_PYWB_OUTPUT.split('\n'):
        ctx.broker.publish(broker.TOPICS.PYWB_OUTPUT, line + '\n')
