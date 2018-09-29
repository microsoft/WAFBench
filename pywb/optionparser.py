# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Option parser

This exports:
    - parse is a function that parses all options and
        delegate them to those enhance parsers.
    - OptionParser is a class, it's an abstract class
        and defines the interfaces. All of option parsers need
        inherit this class.

Option parser of pywb to improve or modify the action which
    is bound to option.
"""

__all__ = [
    "parse",
    "OptionParser",
]

import os
import sys
import abc

import pywbutil


def parse(options, enhance_options):
    """ Parse all options and delegate them to those enhance parsers

    Arguments:
        - options: a list, the command arguments of pywb
        - enhance_options: a dict that key is option and
            the value is option parser of processing arguments
    """

    acceptable_wb_options = "n:c:t:s:b:T:p:u:v:lrkVhwiIx:"\
                            "y:z:C:H:P:A:g:X:de:SqB:m:Z:f:"\
                            "Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:"\
                            "K012:3456789"
    # Anonymous_options are those options without prefix dash.
    # They were not defined at acceptable_wb_option.
    # e.g. destination hostname
    anonymous_options = []
    # Defined_options are those options begin with dash.
    # They were defined at acceptable_wb_option.
    # e.g. -c, -t...
    defined_options = []
    i = 0
    while i < len(options):
        option = options[i]
        i += 1
        if option in enhance_options:  # enhance options
            i += enhance_options[option].load(options[i:])
            continue
        if not option.startswith("-"):  # single option
            anonymous_options.append(option)
            continue
        position = acceptable_wb_options.find(option[1])
        if len(option) != 2 or position == -1:  # invalid option
            raise ValueError("unsupported argument [" + option + "]")
        if position < len(acceptable_wb_options)\
                and acceptable_wb_options[position + 1] == ":":
            # double option
            defined_options.append(option)
            if i >= len(options):
                raise ValueError("option [" + option + "] need an argument")
            option = options[i]
            i += 1
            defined_options.append(option)
            continue
        else:  # single option
            defined_options.insert(0, option)
            continue

    # combine all options
    options = [pywbutil.get_wb_path()]
    for _, trigger in enhance_options.items():
        options += trigger.dump()
    options += defined_options
    options += anonymous_options
    return options


class OptionParser(object):
    """ OptionParser is an abstract class and defines the interfaces.
        All of option parser need inherit this class.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def load(self, arguments):
        """ load the arguments

        Arguments:
            - arguments: a list, the arguments what this action need

        Return is a interger that means the number of this action need
        """
        return 0

    @abc.abstractmethod
    def dump(self):
        """ Dump the new options for wb

        Return a list of string, the options that will be passed to wb
            it's a parameters list. if the space-separated string is inserted
            into the return list, it'll be as just one parameter to pass to wb
        """
        return []

    @abc.abstractmethod
    def help(self):
        """ Help document for this action

        Return is a string of help document for option bound by this instance
        """
        return " "
