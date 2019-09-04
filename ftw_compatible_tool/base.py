#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" base

This exports:
    - BaseConf is a class that contains Base 's configurations.
    - Base is a class that implements ftw_compatible_tool's basic functions.
"""

__all__ = [
    "BaseConf",
    "Base"
]

import uuid
import os
import ast
import re
import sys
import traceback
import collections

import pywb

import context
import broker
import sql
import database
import traffic
import collector


class BaseConf(object):
    """ Contain class Base's configurations.

    Arguments:
        - pkt_path: A path to save the packet(default = test.<pid>.pkt).
        - timeout: An integer means the maximum number of seconds to wait 
            before the socket times out(default = 1).
        - functions: A dict maps commands and functions.
            Key is the name of command.
            Value is the process function.

    Attributes:
        The same with Arguments.
    """
    def __init__(self,
                 pkt_path="test." + str(os.getpid()) + ".pkt",
                 timeout=30,
                 functions={}):

        abspath = os.path.abspath(os.sep)
        abstmp = os.path.join(abspath, "tmp")
        if os.path.exists(abstmp):
            self.pkt_path = os.path.join(abstmp,  pkt_path)
        else:
            curtmp = os.path.join(os.getcwd(), "tmp")
            if not os.path.exists(curtmp):
                os.makedirs(curtmp)
            self.pkt_path = os.path.join(curtmp,  pkt_path)

        self.timeout = timeout
        self.functions = functions


class Base(object):
    """ Implement Basic functions of ftw_compatible_tool

    Arguments:
        - ctx: A Context object.
        - conf: A BaseConf object.

    Attributes:
        - _ctx: A Context object.
        - _conf: A BaseConf Object.
    """
    def __init__(self, ctx, conf=BaseConf()):
        """ Create a Base object.
            And subscribe itself for COMMAND and FATAL.
        """
        self._ctx = ctx
        self._conf = conf

        functions = {
            "load": self._load_yaml_tests,
            "gen": self._gen_requests,
            "start": self._start_experiment,
            "import": self._import_log,
            "report": self._report_experiment,
            "exit": self._exit,
        }
        functions.update(self._conf.functions)
        self._conf.functions = functions
        self._ctx.broker.subscribe(broker.TOPICS.COMMAND, self._command)
        self._ctx.broker.subscribe(broker.TOPICS.FATAL,
                                   self._notification_processor)

    def __del__(self):
        if os.path.exists(self._conf.pkt_path) and os.path.isfile(
                self._conf.pkt_path):
            os.remove(self._conf.pkt_path)
        self._ctx.broker.unsubscribe(broker.TOPICS.COMMAND, self._command)
        self._ctx.broker.unsubscribe(broker.TOPICS.FATAL,
                                     self._notification_processor)

    def _notification_processor(self, *args, **kwargs):
        traceback.print_stack(file=sys.stderr)
        self._ctx.broker.publish(broker.TOPICS.SHOW_UI, "bye")
        sys.exit(-1)

    def _command(self, command, *args, **kwargs):
        if command.lower() in self._conf.functions:
            self._ctx.broker.publish(broker.TOPICS.INFO,
                                     "<%s> ..." % (command, ))
            self._conf.functions[command.lower()](*args, **kwargs)
            return
        self._ctx.broker.publish(
            broker.TOPICS.WARNING, "<%s%s%s> is not internal command" % (
                command,
                " " + str(args) if args else "",
                " " + str(kwargs) if kwargs else "",
            ))

    def _exit(self):
        self._ctx.broker.publish(broker.TOPICS.SHOW_UI, "bye")
        self.__del__()
        sys.exit(0)

    def _load_yaml_tests(self, yaml_paths):
        yaml_paths = os.path.abspath(os.path.expanduser(yaml_paths))
        if not os.path.exists(yaml_paths):
            self._ctx.broker.publish(broker.TOPICS.ERROR,
                                     " %s is not existed " % (yaml_paths, ))
            return
        try:
            for test in pywb.ftwhelper.get(yaml_paths,
                                           pywb.ftwhelper.FTW_TYPE.TEST):
                for stage in pywb.ftwhelper.get(test,
                                                pywb.ftwhelper.FTW_TYPE.STAGE):
                    for packet in pywb.ftwhelper.get(
                            stage, pywb.ftwhelper.FTW_TYPE.PACKETS):
                        self._ctx.broker.publish(
                            broker.TOPICS.SQL_COMMAND,
                            sql.SQL_INSERT_REQUEST,
                            str(uuid.uuid1().int), # traffic_id
                            test["test_title"], # test_title
                            str(test), # meta
                            str(test.ORIGINAL_FILE), # file
                            str(stage['input']), # input 
                            str(stage['output']), # output
                            packet, # request
                        )
        except ValueError as e:
            self._ctx.broker.publish(broker.TOPICS.ERROR, str(e))

    def _gen_requests(self, request_sql_script=None, *args):
        def gen_requests(result=database.QueryResult()):
            with pywb.packetsdumper.PacketsDumper(
                    self._conf.pkt_path) as dumper:
                if "traffic_id" not in result.title(
                ) or "request" not in result.title():
                    self._ctx.broker.publish(
                        broker.TOPICS.ERROR,
                        "sql \"%s\" is not correct for generate testcase" %
                        (request_sql_script, ))
                    return
                for row in result:
                    row = dict(zip(result.title(), row))
                    if self._ctx.delimiter:
                        delimiter_packet = self._ctx.delimiter.get_delimiter_packet(
                            row["traffic_id"])
                        delimiter_packet = pywb.ftwhelper.get(
                            delimiter_packet, pywb.ftwhelper.FTW_TYPE.PACKETS)
                        dumper.dump(delimiter_packet)
                    dumper.dump(row["request"])
                    if self._ctx.delimiter:
                        delimiter_packet = self._ctx.delimiter.get_delimiter_packet(
                            row["traffic_id"])
                        delimiter_packet = pywb.ftwhelper.get(
                            delimiter_packet, pywb.ftwhelper.FTW_TYPE.PACKETS)
                        dumper.dump(delimiter_packet)
        self._ctx.broker.publish(
            broker.TOPICS.SQL_COMMAND,
            request_sql_script
            if request_sql_script else sql.SQL_QUERY_REQUEST,
            *args,
            callback=gen_requests)

    def _start_experiment(self, destination):
        if not os.path.exists(self._conf.pkt_path):
            self._gen_requests()
            if not os.path.exists(self._conf.pkt_path):
                self._ctx.broker.publish(
                    broker.TOPICS.WARNING,
                    " %s is not existed " % (self._conf.pkt_path, ))
                return
        self._ctx.broker.publish(broker.TOPICS.SQL_COMMAND,
                                 sql.SQL_CLEAN_RAW_DATA)
        self._ctx.broker.publish(broker.TOPICS.RESET)

        def collect_pywb_ouput(line):
            self._ctx.broker.publish(broker.TOPICS.PYWB_OUTPUT, line)

        ret = pywb.execute([
            "-F", self._conf.pkt_path, "-v", "4", destination, "-n", "1", "-c",
            "1", "-r", "-s",
            str(self._conf.timeout), "-o", "/dev/null"],
            customized_filters=[collect_pywb_ouput])
        return ret

    def _import_log(self, log):
        log_path = os.path.abspath(os.path.expanduser(log))
        if os.path.exists(log_path):
            with open(log_path, "r") as fd:
                for line in fd:
                    self._ctx.broker.publish(broker.TOPICS.RAW_LOG, line)
        else:
            self._ctx.broker.publish(broker.TOPICS.RAW_LOG, log)

    def _report_experiment(self):
        def check_http_code(item, http_content):
            if not http_content:
                return False
            result = re.search(r"HTTP[\S]+ (\d{3})", http_content)
            if not result:
                return False
            http_code = result.group(1)
            if isinstance(item, list):
                item = list(map(str, item))
                return http_code in item
            else:
                return str(item) == http_code

        def regex_match(item, value):
            return bool(value) and bool(re.search(unicode(item), value, re.MULTILINE))

        def regex_not_match(item, value):
            return not bool(regex_match(item, value))

        check_items = {
            "status": ("raw_response", check_http_code ),
            "log_contains": ("raw_log", regex_match),
            "no_log_contains": ("raw_log", regex_not_match),
            "response_contains": ("raw_response", regex_match),
            "html_contains": ("raw_response", regex_match),
            "expect_error":
            ("raw_response",
             lambda item, value: not (bool(item) and bool(value))),
        }

        def report_experiment(query_result):
            for row in query_result:
                row = collections.OrderedDict(zip(query_result.title(), row))
                # this test not be sent
                if row["raw_request"] is None:
                    continue
                check_result = {}
                try:
                    row["output"] = ast.literal_eval(row["output"])
                    for k, v in row["output"].items():
                        if k not in check_items:
                            continue
                        check_item = check_items[k]
                        check_result[k] = check_item[1](v, row[check_item[0]])
                    self._ctx.broker.publish(
                        broker.TOPICS.SQL_COMMAND,
                        sql.SQL_UPDATE_TESTING_RESULT,
                        str(bool(not check_result \
                        or reduce(lambda x, y: x and y, check_result.values()))),
                        row["traffic_id"]
                        )
                    self._ctx.broker.publish(broker.TOPICS.CHECK_RESULT, row,
                                             check_result)
                except (re.error, SyntaxError) as e:
                    self._ctx.broker.publish(broker.TOPICS.CHECK_RESULT, row,
                                             check_result)
                    self._ctx.broker.publish(broker.TOPICS.WARNING, str(e))

        self._ctx.broker.publish(
            broker.TOPICS.SQL_COMMAND,
            sql.SQL_QUERY_RESULT,
            callback=report_experiment)


