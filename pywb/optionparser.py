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
import packetsloader


def parse(options, enhance_options):
    """ Parse all options and delegate them to those enhance parsers

    Arguments:
        - options: a list, the command arguments of pywb
        - enhance_options: a dict that key is option and
            the value is option parser of processing arguments
    """

    acceptable_options = "n:c:t:s:b:T:p:u:v:lrkVhwiIx:y:z:C:H:P:A:g:X:de:\
SqB:m:Z:f:Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:K012:3456789"
    default_option = []  # default option is those option without prefix dash
    keyword_option = []  # keyword option is those option begin with dash
    i = 0
    while i < len(options):
        option = options[i]
        i += 1
        if option in enhance_options:  # enhance options
            i += enhance_options[option].do(options[i:])
            continue
        if not option.startswith("-"):  # single option
            default_option.append(option)
            continue
        position = acceptable_options.find(option[1])
        if len(option) != 2 or position == -1:  # invalid option
            raise ValueError("unsupported argument [" + option + "]")
        if position < len(acceptable_options)\
                and acceptable_options[position + 1] == ":":  # double option
            keyword_option.append(option)
            if i >= len(options):
                raise ValueError("option [" + option + "] need an argument")
            option = options[i]
            i += 1
            keyword_option.append(option)
            continue
        else:  # single option
            keyword_option.insert(0, option)
            continue
    # combine all options
    options = [pywbutil.get_wb_path()]
    for _, trigger in enhance_options.items():
        options += trigger.dump()
    options += keyword_option
    options += default_option
    return options


class OptionParser(object):
    """ OptionParser is an abstract class and defines the interfaces.
        All of option parser need inherit this class.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def do(self, arguments):
        """ Do the action

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


class PacketFileEnhance(OptionParser):
    """ Packet file parser, enhance option '-F' to
        load multiple options, yaml file and directory

    Arguments:
        - packets_file: a string, the file for storing all packets
            needed sent by wb
    """
    def __init__(self, packets_file):
        """ Create a PacketFileEnhance
        """
        self._packets_file = packets_file
        self._read_packets_paths = []

    def do(self, options):
        """ See OptionParser.do """
        file_count = 0
        while file_count < len(options):
            if options[file_count].startswith("-"):  # is a option
                break
            if not os.path.exists(options[file_count]):  # isn't a file
                break
            self._read_packets_paths.append(options[file_count])
            file_count += 1
        if file_count == 0:
            raise ValueError("-F needs an argument")
        return file_count

    def dump(self):
        """ See OptionParser.dump """
        if not self._read_packets_paths:
            return []
        packetsloader.execute(self._read_packets_paths, self._packets_file)
        return ["-F", self._packets_file]

    def help(self):
        """ See OptionParser.help """
        help_string = "    -F pkt_files    support \"%s\" or direcotries that \
include these kind of files\n" % (",".join(packetsloader.LOADERS.keys()))
        return help_string


class UploadFileEnhance(OptionParser):
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

    def do(self, options):
        file_count = 0
        while file_count < len(options):
            if options[file_count].startswith("-"):  # is a option
                break
            if not os.path.exists(options[file_count]):  # isn't a file
                break
            self._upload_files.append(options[file_count])
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
