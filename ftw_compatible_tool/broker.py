#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" broker
"""

import copy

# TOPICS


class TOPICS(object):
    COMMAND = "COMMAND"
    RESET = "RESET"
    SQL_QUERY = "SQL_QUERY"

    PYWB_OUTPUT = "PYWB_OUTPUT"

    RAW_REQUEST = "RAW_REQUEST"
    RAW_RESPONSE = "RAW_RESPONSE"
    RAW_TRAFFIC = "RAW_TRAFFIC"
    RAW_LOG = "RAW_LOG"

    CHECK_RESULT = "CHECK_RESULT"

    SHOW_UI = "SHOW_UI"

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Broker(object):
    class TopicItem(object):
        def __init__(self, topic):
            self.topic = topic
            self.type_limit = dict()
            self.subscribers = set()

    def __init__(self):
        self._topic_items = {}

    def subscribe(self, topic, subscriber, type_limit={}):
        if not hasattr(subscriber, "__call__"):
            self._ctx.broker.publish(
                TOPICS.FATAL, "subscriber<%s> is not callable" % (subscriber))
            return
        item = self._topic_items.setdefault(topic, Broker.TopicItem(topic))
        if type_limit:
            if item.type_limit and item.type_limit != type_limit:
                self._ctx.broker.publish(
                    TOPICS.FATAL,
                    "type limit<%s> is not compatible with previous<%s>" %
                    (type_limit, ))
                return
            else:
                item.type_limit = type_limit
        item.subscribers.add(subscriber)

    def unsubscribe(self, topic, subscriber):
        if topic not in self._topic_items:
            return
        item = self._topic_items[topic]
        subscribers = item.subscribers
        if subscriber in subscribers:
            subscribers.remove(subscriber)
        if not subscribers:
            del self._topic_items[topic]

    def publish(self, topic, *args, **kwargs):
        item = self._topic_items.get(topic, Broker.TopicItem(topic))
        type_limit = item.type_limit
        subscribers = item.subscribers
        if type_limit:
            type_limit_list = list(type_limit.values())
            for i in range(min(len(type_limit_list), len(args))):
                if not isinstance(args[i], type_limit_list[i]):
                    self._ctx.broker.publish(
                        TOPICS.FATAL,
                        "type<%s> is not compatible with args<%s : (%s)>" %
                        (type_limit, i, args[i]))
                    return
            for k, v in kwargs.items():
                if not isinstance(v, type_limit.get(k, type(v))):
                    self._ctx.broker.publish(
                        TOPICS.FATAL,
                        "type<%s> is not compatible with args<%s : (%s)>" %
                        (type_limit, k, v))
                    return
        tuple(map(lambda subscriber: subscriber(*args, **kwargs), subscribers))


class Subscriber(object):
    def __init__(self, broker, subscribe_items=()):
        self._broker = broker
        self._subscribe_items = subscribe_items

    def start(self):
        for i in self._subscribe_items:
            self._broker.subscribe(*i)

    def end(self):
        for i in self._subscribe_items:
            self._broker.unsubscribe(i[0], i[1])


if __name__ == "__main__":

    class PrintKV(Subscriber):
        def __init__(self, broker):
            super(PrintKV, self).__init__(broker, (("strict", self._print, {
                "fmt": str
            }), ("notstrict", self._print)))

        def _print(self, fmt, key, value):
            print(fmt % (key, value))

    broker = Broker()

    printer = PrintKV(broker)
    printer.start()
    broker.publish("strict", "%d : %s", 1, "tester")
    broker.publish("strict", fmt="%d : %s", key=2, value="tester")

    broker.publish("notstrict", "%d : %s", 3, "tester")
    broker.publish("notstrict", fmt="%d : %s", key=4, value="tester")

    try:
        broker.subscribe("strict", broker)
    except ValueError as e:
        print(e)
    try:
        broker.publish("strict", {"fmt": "%d : %s"}, 5, "tester")
    except ValueError as e:
        print(e)

    try:
        broker.publish("notstrict", {"fmt": "%d : %s"}, 6, "tester")
    except TypeError as e:
        print(e)

    printer.end()
