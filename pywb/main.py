#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Application pywb

This exports:
    - execute_wb is a function that executes wb by a subprocess
    - execute is a function that executes pywb
"""

__all__ = [
    "execute_wb",
    "execute",
]

import sys
import signal
import subprocess
import collections

import optionparser
import outputfilter


def execute_wb(arguments, filters):
    """ execute wb by a subprocess

    Argument:
        - arguments: A string list of the arguments will pass to wb
        - filters: A list of filters to process
            the output of wb

    Return an interger that is return code of wb
    """
    wb = subprocess.Popen(
        arguments, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # capture SIGINT
    signal.signal(signal.SIGINT, lambda signal_, _: wb.send_signal(signal_))
    while True:
        line = wb.stdout.readline()
        if not line:
            break
        for filter_ in filters:
            line = filter_(line)
            if line is None:
                break
    return wb.wait()


def execute(arguments, customized_options={}, customized_filters=[]):
    """ Execute pywb

    Arguments:
        - arguments: a string list of the arguments for pywb
        - customized_options: a dict.
            The type of key is string that means
                which options is supported or modified.
            The type of value is the subclass of OptionParser
                that specified the action for its option.
        - customized_filters: a list of XXXX,
                customized filters for processing the output of wb

    Return an interger that is return code of wb
    """

    enhance_options =\
        collections.OrderedDict([
            ("-F", optionparser.PacketFileEnhance(".default.pkt")),
            ("-p", optionparser.UploadFileEnhance("-p", arguments)),
            ("-u", optionparser.UploadFileEnhance("-u", arguments)),
        ])

    for opt, parser in customized_options.items():
        enhance_options[opt] = parser

    arguments = optionparser.parse(
        arguments,
        enhance_options=enhance_options)

    output_filters = [
        outputfilter.HelpInfoGenerator(enhance_options),
        outputfilter.simple_printer,
    ]

    output_filters = customized_filters + output_filters
    return execute_wb(arguments, output_filters)

if __name__ == '__main__':
    execute(sys.argv[1:])
