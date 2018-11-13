#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" collector

This exports:
    - COLLECT_STATE is an enum that means collector's state.
    - Collector is an abstract class that declares collector's interface.
    - SwitchCollector is an abstract class inherited from Collector 
        that is designed for collecting content with start_pattern and end_pattern.
"""

__all__ = [
    "COLLECT_STATE",
    "Collector",
    "SwitchCollector"
]

import abc
import re


class COLLECT_STATE:
    """ COLLECT_STATE
        FINISH_COLLECT means the collector is ready for a new collecting
        START_COLLECT means the collector is collecting something into buffer.
        PAUSE_COLLECT means the collector has paused
    """
    FINISH_COLLECT = 1
    START_COLLECT = 2
    PAUSE_COLLECT = 3


class Collector(object):
    """ Collector's ABC.

    Attributes:
        - _collected_buffer: A string.
            The buffer for collected things in one turn.
        - state: A COLLECT_STATE value.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """ Initialize buffer and state.
        """
        self._collected_buffer = ""
        self.state = COLLECT_STATE.FINISH_COLLECT

    @abc.abstractmethod
    def __call__(self, line):
        """ Collect or ignore line.

        Arguments:
            - line: A string.
        """
        pass

    def _reset(self):
        """ Reset buffer and state.
        """
        self._collected_buffer = ""
        self.state = COLLECT_STATE.FINISH_COLLECT


class SwitchCollector(Collector):
    """ The Collector designed for collecting content with start_pattern and end_pattern.

    Arguments:
        - start_pattern: If the collector meet string match start_pattern, 
            it starts collecting the next content.
            Should not be empty string.
        - end_pattern: If the collector meet string match end_pattern,
            when it's collecing,
            it stops collecting.
            Should not be empty string.
        
    Attributes:
        - _start_pattern: The re.Pattern object compiled from start_pattern.
        - _end_pattern:  The re.Pattern object compiled from end_pattern.
        - _start_result: Save the last result of matching start_pattern.
        - _end_result: Save the last result of matching end_pattern.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, start_pattern, end_pattern):
        """ Initialize patterns and results.
        """
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
        """ Process the collected.

        Arguments:
            - collected_buffer: A string containing collected content.
            - start_result: A re.Match object. The match result of start_pattern.
            - end_result: A re.Match object. The match result of end_pattern.
        """
        pass

    def __call__(self, line):
        """ Collect line if state is START_COLLECT.
            Start collecting if line matches start_pattern.
            Finish collecing and process the collected if line matches end_pattern.
        
        See Collector.__call__
        """
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
