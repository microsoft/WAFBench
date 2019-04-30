#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import print_function

""" traffic

This exports:
    - REQUEST_PATTERN is a regex string that matches request's start pattern.
    - RESPONSE_PATTERN is a regex string that matches response's start pattern.
    - FINISH_PATTERN is a regex string that matches traffics' end pattern.
    - RawRequestCollector is a class inherited from _RawPacketCollector
        that collects request from pywb's output.
    - RawResponseCollector is a class inerited from _RawPacketCollecotr 
        that collects response from pywb's output.
    - RealTrafficCollector is a class
        that collects each traffic's requests and responses 
        from RawRequestCollector and RawResponseCollector,
        and query database to save.
    - Delimiter is a class that manages delimiters for rules, packets and logs.
"""

__all__ = [
    "REQUEST_PATTERN",
    "RESPONSE_PATTERN",
    "FINISH_PATTERN",
    "RawRequestCollector",
    "RawResponseCollector",
    "RealTrafficCollector",
    "Delimiter",
]

import uuid
import re
import time

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
                broker.TOPICS.WARNING, "package lose message(%s/%s)" %
                (len(collected_buffer), received_size ))
            received_size = len(collected_buffer)
        package = collected_buffer[:received_size]
        self._ctx.broker.publish(self._topic, package)


class RawRequestCollector(_RawPacketCollector):
    """ Collect requests from pywb's output.

    Arguments:
        - ctx: A Context object.
    """
    def __init__(self, ctx):
        super(RawRequestCollector, self).__init__(
            REQUEST_PATTERN, r"(%s)|(%s)|(%s)" %
            (REQUEST_PATTERN, RESPONSE_PATTERN, FINISH_PATTERN),
            broker.TOPICS.RAW_REQUEST, ctx)


class RawResponseCollector(_RawPacketCollector):
    """ Collect responses from pywb's output.

    Arguments:
        - ctx: A Context object.
    """
    def __init__(self, ctx):
        super(RawResponseCollector, self).__init__(
            RESPONSE_PATTERN, r"(%s)|(%s)|(%s)" %
            (RESPONSE_PATTERN, REQUEST_PATTERN, FINISH_PATTERN),
            broker.TOPICS.RAW_RESPONSE, ctx)


class RealTrafficCollector(object):
    """ Collect each traffic's requests and responses.
        Using delimiter request to separate each traffic.

    Arguments:
        - ctx: A Context object.
    
    Attributes:
        - _ctx: A Context object.
        - _current_key: The collecting traffic's id.
        - _request_buffer: Buffer for the collecting traffic's requests.
        - _response_buffer: Buffer for the collecting traffic's responses.
        _ _state: Traffic collect state.
    """
    def __init__(self, ctx):
        """ Create a RealTrafficCollector object.
            Subscribe itself to RAW_REQUEST, RAW_RESPONSE and RESET.
        """
        self._ctx = ctx
        self._current_key = None
        self._request_buffer = ""
        self._response_buffer = ""
        self._request_time = None
        self._response_time = None
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
        elapse_time = None
        if self._request_time and self._response_time:
            elapse_time = self._response_time - self._request_time
        self._ctx.broker.publish(
            broker.TOPICS.SQL_COMMAND,
            sql.SQL_INSERT_RAW_TRAFFIC,
            self._request_buffer,
            self._response_buffer,
            elapse_time,
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
        self._request_time = None
        self._response_time = None
        self._state = collector.COLLECT_STATE.FINISH_COLLECT

    def collect_raw_request(self, raw_request):
        """ Collect requests for each traffic.
            If one traffic's requests are collected,
            publish this traffic's requests and responses to database.

        Arguments:
            - raw_request: A string which is a single request.
        """
        key = self._ctx.delimiter.get_delimiter_key(raw_request)
        if key:
            if self._current_key is None:
                self._current_key = key
            elif self._current_key == key:
                self._publish()
                self._reset()
            else:
                self._ctx.broker.publish(
                    broker.TOPICS.ERROR,
                    "Lose request %s" % (self._current_key))
                return
        else:
            if not self._request_time:
                self._request_time = time.time()
            self._request_buffer += raw_request

    def collect_raw_response(self, raw_response):
        """ Collect responses for each traffic.

        Arguments:
            - raw_resonse: A string which is a single response.
        """
        if self._current_key is None:
            if self._state == collector.COLLECT_STATE.START_COLLECT:
                self._state = collector.COLLECT_STATE.FINISH_COLLECT
        # key was set
        elif self._state == collector.COLLECT_STATE.FINISH_COLLECT:
            self._state = collector.COLLECT_STATE.START_COLLECT
        elif self._state == collector.COLLECT_STATE.START_COLLECT:
            if self._request_buffer:
                if not self._response_time:
                    self._response_time = time.time()
                self._response_buffer += raw_response

        else:
            self._ctx.broker.publish(broker.TOPICS.ERROR,
                                     "Internal state error")
            return


class Delimiter(object):
    """ Manages delimiters used to separate each traffic.

    Arguments:
        - magic_string: An abnormal string that no normal operations will use.
            We use this string to identify our delimiter.
        
    Attributes:
        - _magic_string: Same as magic_string.
        - _magic_searcher: A re.Pattern object.
            We use this to search our delimiter.
    """
    _MAGIC_PATTERN = r"{magic_string}-{unique_key}"

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
    "phase:1,\
    id:010203,\
    t:none,\
    deny,\
    msg:'delimiter-%{{matched_var}}'"
    '''

    @staticmethod
    def _generate_magic_string():
        return "%s" % (uuid.uuid1().int, )

    def __init__(self, magic_string=None):
        """ Create a Delimiter object.
            Initialize the magic's string for delimiters.
        """
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
        """ Return the rule that should be inserted into ModSecurity's conf file's head,
            used for generating delimiter in log.
        """
        return Delimiter._DELIMITER_RULE_FORMAT.format(
            **{"magic_pattern": self._magic_searcher.pattern})

    def get_delimiter_key(self, line):
        """ Check whether line is a delimiter line.

        Arguments:
            - line: A string to be checked.

        Return the delimiter's key(unique id) if the line is a delimiter line,
        otherwise return None.
        """
        result = self._magic_searcher.search(line)
        if result:
            return result.group(1)
        else:
            return None

    def get_delimiter_packet(self, key):
        """ Return the packet that should be sent before and after one traffic,
            used for generating delimiter in requests, responses and logs.

        Arguments:
            - key: The traffic's unique id.
            
        Return packet is a string in yaml format.
        """
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
        """ Return the delimiter's log msg that separates each traffic.
        """
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

    ctx.broker.subscribe(broker.TOPICS.SQL_COMMAND, PrintMessage)

    for line in testdata.TEST_PYWB_OUTPUT.split('\n'):
        ctx.broker.publish(broker.TOPICS.PYWB_OUTPUT, line + '\n')
