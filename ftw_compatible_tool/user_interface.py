#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" user_interface

This exports:
     - Interactor is an abstract class that declares Interactor's interfaces.
     - CLI is a class inherited from Interactor
        that implement ftw_compatible_tool's user interface.
"""

__all__ = [
    "Interactor",
    "CLI"
]

import re
import os
import sys
import abc
import textwrap
import shlex
import collections
import readline
import glob
import math

import context
import sql
import broker
import traffic
from functools import reduce


class Interactor(object):
    """ Interactor's ABC.

    Arguments:
        - ctx: A Context object.
    
    Attributes:
        - _ctx: Same as ctx.
        - _current_progress_monitor: A callable object
            with arguments(traffic_id, raw_request, raw_response),
            used for showing progress.
        - _components: A dict mapping ui name to ui function.
            Key is a string meaning a kind of ui.
            Value is a callable object implementing a kind of ui.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, ctx):
        """ Initialize self and subscribe itself to SHOW_UI, CHECK_RESULT and PYWB_OUTPUT.
        """
        self._ctx = ctx
        self._current_progress_monitor = None
        self._ctx.broker.subscribe(broker.TOPICS.CHECK_RESULT,
                                   self._print_check_result)
        self._ctx.broker.subscribe(broker.TOPICS.PYWB_OUTPUT,
                                   self._progress_monitor)
        self._components = {}
        self._ctx.broker.subscribe(
            broker.TOPICS.SHOW_UI,
            self._show_ui,
        )

    def __del__(self):
        self._ctx.broker.unsubscribe(broker.TOPICS.CHECK_RESULT,
                                     self._print_check_result)
        self._ctx.broker.unsubscribe(broker.TOPICS.PYWB_OUTPUT,
                                     self._progress_monitor)
        self._ctx.broker.unsubscribe(
            broker.TOPICS.SHOW_UI,
            self._show_ui,
        )
        if self._current_progress_monitor is not None:
            self._ctx.broker.unsubscribe(broker.TOPICS.RAW_TRAFFIC,
                                         self._current_progress_monitor)

    def _show_ui(self, component, *args, **kwargs):
        if component not in self._components:
            return
        self._components[component](*args, **kwargs)

    def _progress_monitor(self, line):
        def progress_monitor(traffic_id, raw_request, raw_response):
            def show_progress(query_result):
                title = str(traffic_id)
                for row in query_result:
                    title = row[0]
                self._report_progress(self._traffic_finished,
                                      self._traffic_count, title)

            self._traffic_finished += 1
            self._ctx.broker.publish(
                broker.TOPICS.SQL_COMMAND,
                sql.SQL_QUERY_TEST_TITLE,
                traffic_id,
                callback=show_progress)

        result = re.search(
            r"^ read (\d+) packets from file with total length\((\d+)\)\.$",
            line)
        if result:
            line = line[result.end()]
            self._traffic_count = int(result.group(1)) / 3
            self._traffic_finished = 0
            if self._current_progress_monitor is not None:
                self._ctx.broker.unsubscribe(broker.TOPICS.RAW_TRAFFIC,
                                             self._current_progress_monitor)
            self._current_progress_monitor = progress_monitor
            self._ctx.broker.subscribe(broker.TOPICS.RAW_TRAFFIC,
                                       self._current_progress_monitor)
        result = re.search(traffic.FINISH_PATTERN, line)
        if result:
            line = line[result.start()]
            if self._current_progress_monitor is not None:
                self._ctx.broker.unsubscribe(broker.TOPICS.RAW_TRAFFIC,
                                             self._current_progress_monitor)
            self._traffic_count = 0
            self._traffic_finished = 0

    @abc.abstractmethod
    def _print_check_result(self, traffic, check_result):
        pass

    @abc.abstractmethod
    def _report_progress(self, current, total, title):
        pass

    @abc.abstractmethod
    def interact(self):
        pass


class CLI(Interactor):
    """ ftw_compatible_tool's user interface.

    Arguments:
        - ctx: A Context object.

    Attributes:
        See Interactor for the same attributes.
        - _debug: Function for debug ui.
        - _info: Function for info ui.
        - _warning: Function for warning ui.
        - _error: Function for error ui.
        - _fatal: Function for fatal ui.
    """
    class STYLE:
        """ Define ui's style. Most of them are easy to see meaning.
            Simply print them can do the work.
            
            RESET means to clear style set before.
        """
        RESET = '\033[0m'
        BOLD = '\033[01m'
        UNDERLINE = '\033[04m'

        class FG:
            """ Define frontground's color.
            """
            BLACK = '\033[30m'
            RED = '\033[31m'
            YELLOW = '\033[93m'
            CYAN = '\033[36m'
            BLUE = '\033[34m'
            GREEN = '\033[32m'
            MAGENTA = '\033[35m'

        class BG:
            """ Define background's color.
            """
            RED = '\033[41m'
            LIGHTGREY = '\033[47m'

    def __init__(self, ctx):
        """ Create a CLI object.
            Subscribe itself to DEBUG, INFO, WARNING, ERROR and FATAL.
        """
        super(CLI, self).__init__(ctx)
        self._components.update({
            "welcome": self._welcome,
            "bye": self._bye,
            "tutorial": self._tutorial,
            "print_query_result": self._print_query_result
        })
        self._debug = self._message_notifier(CLI.STYLE.FG.CYAN)
        self._info = self._message_notifier(CLI.STYLE.FG.GREEN)
        self._warning = self._message_notifier(CLI.STYLE.FG.YELLOW)
        self._error = self._message_notifier(CLI.STYLE.FG.RED)
        self._fatal = self._message_notifier(CLI.STYLE.FG.RED +
                                             CLI.STYLE.UNDERLINE)
        self._ctx.broker.subscribe(broker.TOPICS.DEBUG, self._debug)
        self._ctx.broker.subscribe(broker.TOPICS.INFO, self._info)
        self._ctx.broker.subscribe(broker.TOPICS.WARNING, self._warning)
        self._ctx.broker.subscribe(broker.TOPICS.ERROR, self._error)
        self._ctx.broker.subscribe(broker.TOPICS.FATAL, self._fatal)

    def __del__(self):
        self._ctx.broker.unsubscribe(broker.TOPICS.DEBUG, self._debug)
        self._ctx.broker.unsubscribe(broker.TOPICS.INFO, self._info)
        self._ctx.broker.unsubscribe(broker.TOPICS.WARNING, self._warning)
        self._ctx.broker.unsubscribe(broker.TOPICS.ERROR, self._error)
        self._ctx.broker.unsubscribe(broker.TOPICS.FATAL, self._fatal)
        return super(CLI, self).__del__()

    def _message_notifier(self, color):
        def message_notifier(*args, **kwargs):
            sys.stderr.write(color + "MESSAGE:" + CLI.STYLE.BOLD)
            if args:
                sys.stderr.write(str(args) if len(args) > 1 else args[0])
            if kwargs:
                sys.stderr.write(str(kwargs))
            sys.stderr.write(CLI.STYLE.RESET + "\n")

        return message_notifier

    def _MAX_SIZE(self):
        return tuple(map(int, os.popen('stty size', 'r').read().split()))

    def _welcome(self):
        print(r'''
________________________      __          _________
\_   _____/\__    ___/  \    /  \         \_   ___ \  ____   _____ ______
 |    __)    |    |  \   \/\/   /  ______ /    \  \/ /  _ \ /     \\____ \
 |     \     |    |   \        /  /_____/ \     \___(  <_> )  Y Y  \  |_> >
 \___  /     |____|    \__/\  /            \______  /\____/|__|_|  /   __/
     \/                     \/                    \/             \/|__|
            ''')

    def _bye(self):
        print("")
        print("~" * int(self._MAX_SIZE()[1] * 0.5))
        print("bye~")

    def _print_query_result(self, query_result):
        print(query_result.title())
        for row in query_result:
            print(row)

    def _report_progress(self, finished, total, title):
        if finished > total:
            self._ctx.broker.publish(
                broker.TOPICS.WARNING,
                "Finished(%s) over total(%s) : %s" % (finished, total, title))
            return

        total_len = int(self._MAX_SIZE()[1] * 0.6)
        done_filling = ' '
        undone_filling = '-'

        percent_len = len("100.0%")
        filling_len = total_len - percent_len - 2
        title = "(%s)" % (title)
        if len(title) > filling_len:
            title = title[:filling_len - 4] + "...)"
        title_len = len(title)
        percent = float(int(float(finished) / float(total) * 1000)) / 1000.0
        done_filling_len = int(max(percent * filling_len - title_len, 0))
        undone_filling_len = int(
            max(filling_len - title_len - done_filling_len, 0))
        buffer_ = "[{title}{done_filling}{undone_filling}]{percent}%"
        buffer_ = buffer_.format(
            title=title,
            done_filling=done_filling * done_filling_len,
            undone_filling=undone_filling * undone_filling_len,
            percent=("%s" % (100.0 * percent, )).rjust(
                len("100.0"))[:len("100.0")],
        )
        # insert style
        buffer_ = buffer_[:1] \
            + CLI.STYLE.BG.LIGHTGREY\
            + CLI.STYLE.FG.BLACK \
            + buffer_[1:int(math.ceil(percent * filling_len))] \
            + CLI.STYLE.RESET \
            + buffer_[int(math.ceil(percent * filling_len)):]
        sys.stdout.write("\r" + self._MAX_SIZE()[1] * ' ')
        if finished == total:
            sys.stdout.write(buffer_ + "\n")
        else:
            sys.stdout.write("\r" + buffer_)
        sys.stdout.flush()

    def _tutorial(self):
        tutorials = (
            ("Add this rule into the head of SecRule(Optional, for white-box testing)\n" +
             self._ctx.delimiter.get_delimiter_rule(), ),
            (
                "Import testcases, "
                "if database has imported some testcases, "
                "the old testcases would not be overwritten",
                "load <PATH of testcases>",
                "load ./OWASP-CRS-regressions",
            ),
            (
                "Generate .pkt file,"
                "you can specify which testcases you want to test by SQL script("
                "default is \"" + sql.SQL_QUERY_REQUEST.strip() + "\")",
                "gen [SQL]",
                "gen",
            ),
            (
                "Start test, send request to server",
                "start [hostname]",
                "start localhost:18080",
            ),
            ("Import server log, copy or mount server log to local.(Optional, for white-box testing)",
             "import <PATH of log>",
             "import ~/testbed/default-nginx-1.11.5-ModSecurity-original/logs/error.log"
             ),
            (
                "Report test result",
                "report",
                "report",
            ),
            (
                "Exit program",
                "exit",
                "exit",
            ),
        )
        print("FTW-compatible-tool include %d steps:" % (len(tutorials), ))

        for i in range(len(tutorials)):
            if len(tutorials[i]) == 1:
                tutorial_format = "{step}. {description}\n"
                print(tutorial_format.format(
                    step=i + 1,
                    description=tutorials[i][0],
                ))
            elif len(tutorials[i]) == 3:
                tutorial_format = "{step}. {description}\n   command : {command}\n   e.g. : " + \
                    CLI.STYLE.UNDERLINE + "{example}" + CLI.STYLE.RESET + "\n"
                print(tutorial_format.format(
                    step=i + 1,
                    description=tutorials[i][0],
                    command=tutorials[i][1],
                    example=tutorials[i][2],
                ))

    def _print_check_result(self, traffic, check_result):
        # All check is OK
        if not check_result \
                or reduce(lambda x, y: x and y, check_result.values()):
            return
        traffic = collections.OrderedDict(traffic)
        wrapper = textwrap.TextWrapper()
        wrapper.width = self._MAX_SIZE()[1]
        indent = len(max(traffic.keys(), key=len))
        # '+3' for two spaces and a colon
        wrapper.subsequent_indent = ' ' * (indent + 3)
        for k, v in traffic.items():
            prefix = CLI.STYLE.BOLD \
                + k.ljust(indent) \
                + CLI.STYLE.RESET
            wrapper.initial_indent = prefix + " : "

            buffer_ = ""
            if k == "output":
                buffer_ += "{"
                len_ = len(v.keys())
                for k, v in v.items():
                    if not check_result[k]:
                        buffer_ += CLI.STYLE.BG.RED + CLI.STYLE.BOLD
                    buffer_ += "%s: %s" % (k, repr(v))
                    buffer_ += CLI.STYLE.RESET
                    len_ -= 1
                    if len_ != 0:
                        buffer_ += ", "
                buffer_ = buffer_.strip()
                buffer_ += "}"
            elif isinstance(v, str) or isinstance(v, unicode):
                v = repr(v)
                buffer_ += v
            else:
                buffer_ += str(v)
            print(wrapper.fill(buffer_))
        print("\n")

    def interact(self):
        """ Start interactive user interface.
        """
        def auto_completer(text, state):
            text = text.lower()
            keywords = [
                "load",
                "gen",
                "start",
                "import",
                "report",
                "exit",
            ]
            if text:
                candidates = [
                    candidate for candidate in keywords
                    if candidate.startswith(text)
                ]
            else:
                candidates = keywords
            if state < len(candidates):
                return candidates[state]
            return None

        readline.parse_and_bind("tab: complete")
        readline.set_completer(auto_completer)
        while True:
            try:
                command_buffer = raw_input("\nInput command : ")
                if not command_buffer:
                    continue
            except (KeyboardInterrupt, EOFError):
                print("")
                self._ctx.broker.publish(broker.TOPICS.COMMAND, "exit")
            try:
                command_buffer = shlex.split(command_buffer)
            except ValueError as e:
                print(e)
            try:
                self._ctx.broker.publish(broker.TOPICS.COMMAND,
                                         *command_buffer)
            except TypeError as e:
                print(e)


if __name__ == "__main__":
    import testdata

    ctx = context.Context(
        broker.Broker(),
        delimiter=traffic.Delimiter("334787923864975794240893756898805143302"))
    ui = CLI(ctx)

    traffic.RawRequestCollector(ctx)
    traffic.RawResponseCollector(ctx)
    traffic.RealTrafficCollector(ctx)

    ctx.broker.publish(broker.TOPICS.SHOW_UI, "welcome")
    ctx.broker.publish(broker.TOPICS.CHECK_RESULT, {
        "output": {
            "a": "b",
            "b": "c",
        },
        "title": "title"
    }, {
        "a": True,
        "b": False,
    })

    for line in testdata.TEST_PYWB_OUTPUT.split('\n'):
        ctx.broker.publish(broker.TOPICS.PYWB_OUTPUT, line + "\n")

    ctx.broker.publish(broker.TOPICS.SHOW_UI, "bye")
