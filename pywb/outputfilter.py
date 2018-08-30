# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Output filter Process the output of wb.

This exports:
    - OutputFilter is a class, it's an abstract class
        and defines the interfaces.

All of option filters will inherit OutputFilter or just
    a simple function whose argument and return value are both string.
    The argument is a line of output of wb, and the return value will be
    passed to next filter.
"""

import sys
import re
import abc

__all__ = ["OutputFilter"]


class OutputFilter(object):
    """ Process the output of wb
        Line by line to process the output of wb.
        It's not recommended to modify the line, because it maybe
        conflict with other filters

    Arguments:
        line: a line of string end with '\n' from the output of wb,
            the concrete content depends on the runtime of wb.

    Return is a string. If the return is None, this filter will be a
        terminator, which means that all of the filters after this will
        lose the information of this lien.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, line):
        return line


def simple_printer(line):
    """ This function is the last filter.
        It will print lines received by it.

    Arguments:
        - line: is a string what he will print.
    """
    if line is not None:
        sys.stdout.write(line)
    return None


class HelpInfoGenerator(OutputFilter):
    """ Generate the help info based on the wb help info.

    """
    def __init__(self, enhance_options):
        self._buffer = ""
        self._ignore = False
        self._enhance_options = enhance_options
        self._print_new_option = False

    def _replace_executable(self, line):
        """ Replace executable of Usage from wb to pywb """
        pattern = r"^(Usage:\s*)(\S+)(.*)"
        new_usage = re.sub(pattern, r"\1" + sys.argv[0] + r"\3", line)
        if new_usage != line:
            return new_usage
        else:
            return line

    def _replace_enhance_options(self, line):
        """ Help of enhance options """
        # detect new options
        pattern = r"New options for wb"
        if re.match(pattern, line):
            self._print_new_option = True
            return line
        # print new help
        if self._print_new_option:
            for _, option in self._enhance_options.items():
                line += option.help()
            self._print_new_option = False
            return line

        # remove old help
        pattern = r"^\s{4}(-\w)"
        opt = re.search(pattern, line)
        if opt:
            opt = opt.group(1)
            if opt in self._enhance_options:
                self.__ignore = True
            else:
                self.__ignore = False
        # first char isn't a space, need cancel ignore
        pattern = r"^\S"
        if re.match(pattern, line):
            self.__ignore = False
        # ignore this line
        if self.__ignore:
            return None
        return line

    def __call__(self, line):
        if line is None:
            return None
        replace_filters = [
            self._replace_executable,
            self._replace_enhance_options,
        ]
        for filter_ in replace_filters:
            new_line = filter_(line)
            if new_line != line:
                return new_line
        return line
