#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" collector
"""

import abc
import re


class COLLECT_STATE:
    FINISH_COLLECT = 1
    START_COLLECT = 2
    PAUSE_COLLECT = 3


class Collector(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._collected_buffer = ""
        self.state = COLLECT_STATE.FINISH_COLLECT

    @abc.abstractmethod
    def __call__(self, line):
        pass

    def _reset(self):
        self._collected_buffer = ""
        self.state = COLLECT_STATE.FINISH_COLLECT


class SwitchCollector(Collector):
    __metaclass__ = abc.ABCMeta

    def __init__(self, start_pattern, end_pattern):
        super(SwitchCollector, self).__init__()
        self._start_pattern = re.compile(start_pattern)
        self._end_pattern = re.compile(end_pattern)
        if self._start_pattern.match("") and self._end_pattern.match(""):
            raise ValueError(
                "It's not supported that start and end both are empty"
                " but '%s' and '%s' will both match empty string" %
                (start_pattern, end_pattern))
        self._start_result = None
        self._end_result = None

    @abc.abstractmethod
    def _execute(self, collected_buffer, start_result, end_result):
        pass

    def __call__(self, line):
        while line:
            if self.state == COLLECT_STATE.FINISH_COLLECT:
                self._start_result = self._start_pattern.search(line)
                if self._start_result:
                    self.state = COLLECT_STATE.START_COLLECT
                    line = line[self._start_result.end():]
                else:
                    break
            elif self.state == COLLECT_STATE.START_COLLECT:
                self._end_result = re.search(self._end_pattern, line)
                if self._end_result:
                    self._collected_buffer += line[:self._end_result.start()]
                    line = line[self._end_result.start():]
                    self._execute(self._collected_buffer, self._start_result,
                                  self._end_result)
                    self._reset()
                else:
                    self._collected_buffer += line
                    line = ""
            else:
                break

    def _reset(self):
        super(SwitchCollector, self)._reset()
        self._start_result = None
        self._end_result = None


if __name__ == "__main__":

    class PrintNumber(SwitchCollector):
        def _execute(self, collected_buffer, start_result, end_result):
            print(start_result.group(0))
            print("<%d>" % (int(collected_buffer), ))
            print(end_result.group(0))

    printer = PrintNumber(r"\D+", r"\D+")
    printer("0abc1")
    printer("23")
    printer("456ef7gh8")
