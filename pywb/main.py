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

import os
import sys
import re
import signal
import subprocess
import collections

import optionparser
import outputfilter
import packetsloader
import packetsdumper
import pywbutil


class _PacketFileEnhance(optionparser.OptionParser):
    """ Packet file parser, enhance option '-F' to
        load multiple options, yaml file and directory

    Arguments:
        - packets_file: a string, the file for storing all packets
            needed sent by wb
    """
    def __init__(self, packets_file):
        """ Create a _PacketFileEnhance
        """
        self._packets_file = packets_file
        self._read_packets_paths = []

    def load(self, options):
        """ See OptionParser.do """
        file_count = 0
        while file_count < len(options):
            if options[file_count].startswith("-"):  # is a option
                break
            path_ = options[file_count]
            path_ = os.path.expanduser(path_)
            if not os.path.exists(path_):  # isn't a file
                break
            self._read_packets_paths.append(path_)
            file_count += 1
        if file_count == 0:
            raise ValueError("-F needs an argument")
        return file_count

    def dump(self):
        """ See OptionParser.dump """
        if not self._read_packets_paths:
            return []
        with packetsdumper.PacketsDumper(self._packets_file) as dumper:
            for packet in\
                    packetsloader.load_packets_from_paths(
                        self._read_packets_paths):
                dumper.dump(packet)
        return ["-F", self._packets_file]

    def help(self):
        """ See OptionParser.help """
        help_string = "    -F pkt_files    support \"%s\" or directories that \
include these kind of files\n" % (",".join(packetsloader.LOADERS.keys()))
        return help_string


class _UploadFileEnhance(optionparser.OptionParser):
    """ Upload file parser, enhance option '-p' and -u'
        to automatically inferring the Content-Type by file ext,
        '-p' means to post files and '-u' means to put files.
        <Current version just supports to upload one files>

    Arguments:
        - options: a list, the command arguments of pywb

    Attributes:
        - _action: a string means to post or to put
        - _upload_files: a list,
    """
    def __init__(self, action, options):
        if action not in ["-p", "-u"]:
            raise ValueError(
                self.__class__.__name__
                + " doesn't support action : "
                + action)
        self._action = action
        self._upload_files = []
        self._content_type_modified = False
        if "-T" in options:
            self._content_type_modified = True

    def load(self, options):
        file_count = 0
        while file_count < len(options):
            if options[file_count].startswith("-"):  # is a option
                break
            path_ = options[file_count]
            path_ = os.path.expanduser(path_)
            if not os.path.exists(path_):  # isn't a file
                break
            self._upload_files.append(path_)
            file_count += 1
        if file_count == 0:
            raise ValueError(self._action + " needs an argument")
        return file_count

    def dump(self):
        if not self._upload_files:
            return []
        if len(self._upload_files) > 1:
            sys.stderr.write("<Current version just\
supports to upload one files>")
        upload_file = self._upload_files[0]
        upload_file = os.path.expanduser(upload_file)
        if not os.path.exists(upload_file):
            raise IOError(upload_file + " isn't exist")
        # if Content-Type is set, we don't need automatic inferring
        if self._content_type_modified:
            return [self._action, upload_file]

        file_ext = os.path.splitext(upload_file)[-1].lower()
        content_type = "application/octet-stream"
        if file_ext in pywbutil.MIME_TYPE_DICT:
            content_type = pywbutil.MIME_TYPE_DICT[file_ext]
        return [self._action, upload_file, "-T", content_type]

    def help(self):
        if self._action == "-p":
            return "    -p postfile     File containing data to POST. "\
                + "Content-Type will be detected by file ext,\n"\
                + "                    the Content-Type will be "\
                + "application/octet-stream if file ext cannot be identified\n"
        elif self._action == "-u":
            return "    -u putfile      File containing data to PUT. "\
                + "Content-Type will be detected by file ext,\n"\
                + "                    the Content-Type will be "\
                + "application/octet-stream if file ext cannot be identified\n"
        else:
            raise ValueError("action isn't specified")


def _simple_printer(line):
    """ This function is the last filter.
        It will print lines received by it.

    Arguments:
        - line: is a string what he will print.
    """
    if line is not None:
        sys.stdout.write(line)
    return None


class _HelpInfoGenerator(outputfilter.OutputFilter):
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
    # ignore SIGINT
    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while True:
        line = wb.stdout.readline()
        if not line:
            break
        for filter_ in filters:
            line = filter_(line)
            if line is None:
                break
    # recover SIGINT
    signal.signal(signal.SIGINT, original_handler)
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
        - customized_filters: a list of OutputFilters,
                customized filters for processing the output of wb

    Return an interger that is return code of wb
    """

    enhance_options =\
        collections.OrderedDict([
            ("-F", _PacketFileEnhance(".default.pkt")),
            ("-p", _UploadFileEnhance("-p", arguments)),
            ("-u", _UploadFileEnhance("-u", arguments)),
        ])

    for opt, parser in customized_options.items():
        enhance_options[opt] = parser

    arguments = optionparser.parse(
        arguments,
        enhance_options=enhance_options)

    output_filters = [
        _HelpInfoGenerator(enhance_options),
        _simple_printer,
    ]

    output_filters = customized_filters + output_filters
    return execute_wb(arguments, output_filters)

if __name__ == '__main__':
    sys.exit(execute(sys.argv[1:]))
