#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" broker

This exports:
    - TOPICS is an enum that means various message kinds.
    - Broker is a class that forwards messages among components.
    - Subscriber is a class that receive messages from Broker.

We use Broker Pattern to realize messages' flexibile transmitting.
"""

__all__ = [
    "TOPICS",
    "Broker",
    "Subscriber"
]

import copy
import inspect
import types

# TOPICS


class TOPICS(object):
    """ TOPICS
        COMMAND means user's command
        RESET means to reset ftw_compatible_tool
        SQL_COMMAND means a sql query

        PYWB_OUTPUT means the output from pywb

        RAW_REQUEST means the requests sent by ftw_compatible_tool
        RAW_RESPONSE means the responses from the server
        RAW_TRAFFIC means a traffic including requests and responses with an unique id
        RAW_LOG means ModSecurity's error log
        
        CHECK_RESULT means to show the result of checking output

        SHOW_UI means to show specific UI

        DEBUG, INFO, WARNING, ERROR, FATAL mean log info.
    """
    COMMAND = "COMMAND"
    RESET = "RESET"
    SQL_COMMAND = "SQL_COMMAND"

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
    """ Forward messages to subscribers.

    Attributes:
        - _topic_items: a dict mapping TOPIC to subscribers.
            Key is a TOPICS value.
            Value is a TopicItem object.
    """
    class TopicItem(object):
        """ Store a topic's subscribers.

        Argument:
            - topic: a TOPICS value.
            - type_limit: a dict containing the topic's arguments' proper types.
                Key is the argument's name.
                Value is the type that the argument should be.
            - subscribers: a set containing this topic's subscribers.
        """
        def __init__(self, topic):
            self.topic = topic
            self.type_limit = dict()
            self.subscribers = set()

    def __init__(self):
        """ Create a Broker.
        """
        self._topic_items = {}

    def subscribe(self, topic, subscriber, type_limit={}):
        """ Subscribe the subscriber to the topic.

        Aruguments:
            - topic: A TOPICS value.
            - subscriber: A callable object, e.g. a function.
        """
        if not hasattr(subscriber, "__call__"):
            raise ValueError("subscriber<%s> is not callable" % (subscriber))
        item = self._topic_items.setdefault(topic, Broker.TopicItem(topic))
        if type_limit:
            if len(item.subscribers) > 0 and item.type_limit != type_limit:
                raise ValueError("type limit<%s> is not compatible with previous<%s>" %
                    (type_limit, item.type_limit))
            else:
                item.type_limit = type_limit
        item.subscribers.add(subscriber)

    def unsubscribe(self, topic, subscriber):
        """ Unsubscribe the subscriber from the topic.
            If the subscriber has not subscribed the topic, nothing will happen.

        Aruguments:
            - topic: A TOPICS value.
            - subscriber: A callable object, e.g. a function.
        """
        if topic not in self._topic_items:
            return
        item = self._topic_items[topic]
        subscribers = item.subscribers
        if subscriber in subscribers:
            subscribers.remove(subscriber)
        if not subscribers:
            del self._topic_items[topic]

    def publish(self, topic, *args, **kwargs):
        """ Publish messages to the topic's subscribers.

        Arguments:
            - topic: A TOPICS value.
            - args, kwargs: Arguments sent to subscribers.
                Type check will be done on these.
        """
        item = self._topic_items.get(topic)
        if item is None or len(item.subscribers) == 0:
            return False
        type_limit = item.type_limit
        subscribers = item.subscribers
        if type_limit:
            for subscriber in subscribers:
                if isinstance(subscriber, types.FunctionType):
                    target_args = inspect.getargspec(subscriber).args
                else:
                    target_args = inspect.getargspec(subscriber.__call__).args
                for i in range(min(len(args), len(target_args))):
                    if not isinstance(args[i], type_limit.get(target_args[i], type(args[i]))):
                        raise ValueError(
                            "type<%s> is not compatible with args<%s : (%s)>" %
                            (type_limit, i, args[i]))
                for k, v in kwargs.items():
                    if not isinstance(v, type_limit.get(k, type(v))):
                        raise ValueError(
                            "type<%s> is not compatible with args<%s : (%s)>" %
                            (type_limit, k, v))
        tuple(map(lambda subscriber: subscriber(*args, **kwargs), subscribers))
        return True


class Subscriber(object):
    """ Manage subscribing and unsubscribing of a kind of subscribers.

    Arguments:
        - borker: A Borker object.
        - subscribe_items: A tuple. A list of
            the tuples of topic, subscriber and type_limit.
            To be managed by this Subscriber.
    """
    def __init__(self, broker, subscribe_items=()):
        """ Create a Subscriber.
        """
        self._broker = broker
        self._subscribe_items = subscribe_items

    def start(self):
        """ Subscribe the subscribers that this SubScriber is managing.
        """
        for i in self._subscribe_items:
            self._broker.subscribe(*i)

    def end(self):
        """ Unsubscribe the subscribers that this SubScriber is managing.
        """
        for i in self._subscribe_items:
            self._broker.unsubscribe(i[0], i[1])

