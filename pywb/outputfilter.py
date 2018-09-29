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
        lose the information of this line.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, line):
        return line
