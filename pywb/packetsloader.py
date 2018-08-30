#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Load multiple packets into a packets generator

This exports:
    - load_ftw_rules_from_strings: load a set of yaml strings
        required by ftw to a ftw.Ruleset generator
    - load_ftw_rules_from_files: is a function that load
        a set of files contains yaml files required by ftw
        to a ftw.Ruleset generator
    - load_ftw_rules_from_directories: is a function that load
        a set of directories contains yaml files required by ftw
        to a ftw.Ruleset generator
    - load_ftw_rules_from_paths: is a function that load
        a set of paths contains yaml files required by ftw
        to a ftw.Ruleset generator
    - load_ftw_tests_from_paths: is a function that load
        a set of paths contains yaml files required by ftw
        to a ftw.Test generator
    - load_ftw_stages_from_paths: is a function that load
        a set of paths contains yaml files required by ftw
        to a ftw.Stage generator
    - load_packets_from_yaml_files: is a function that load
        a set of yaml files required by ftw to a packets generator
    - load_packets_from_pkt_files: is a function that load
        a set of .pkt files to a packets generator
    - LOADERS: is a dict, the key is file extension of supported files
        of loader. the value is the load function that create
        a packets generator from file.
    - load_packets_from_paths: is a function that load a set of paths
        that include .pkt or .yaml files to a packets generator.
    - execute: is a function that export all of packets
        into the exporter

Load packets saved in files(.yaml, .pkt) or strings into a packets generator
"""

__all__ = [
    "load_ftw_rules_from_strings",
    "load_ftw_rules_from_files",
    "load_ftw_rules_from_directories",
    "load_ftw_rules_from_paths",
    "load_ftw_tests_from_paths",
    "load_ftw_stages_from_paths",
    "load_packets_from_yaml_files",
    "load_packets_from_pkt_files",
    "LOADERS",
    "load_packets_from_paths",
    "execute",
]

import os
import io
import sys
import functools

import ftw
import yaml

import packetsexporter


def _accept_iterable(func):
    @functools.wraps(func)
    def _decorator(iterable_):
        if not hasattr(iterable_, "__iter__"):
            iterable_ = [iterable_]
        return func(iterable_)
    return _decorator


def _expand_nest_iterable(func):
    @functools.wraps(func)
    def _decorator(*args, **kw):
        iterable_ = func(*args, **kw)
        if not hasattr(iterable_, "__iter__"):
            yield iterable_
        else:
            iterable_ = iterable_.__iter__()
            visit_stack = [iterable_]
            while visit_stack:
                iterable_ = visit_stack[-1]
                if not hasattr(iterable_, "__iter__"):
                    yield iterable_
                    visit_stack.pop()
                else:
                    try:
                        iterable_ = next(iterable_)
                        if hasattr(iterable_, "__iter__"):
                            iterable_ = iterable_.__iter__()
                        visit_stack.append(iterable_)
                    except StopIteration:
                        visit_stack.pop()
    return _decorator


@_accept_iterable
@_expand_nest_iterable
def load_ftw_rules_from_strings(strings):
    """ Load a set of yaml strings required by ftw
         to a ftw.Ruleset generator

    Arguments:
        strings: a set of yaml strings required by ftw

    Return a ftw.Ruleset generator
        that will generate all of ftw.Ruleset
         included in those yaml strings
    """
    for string_ in strings:
        rule = ftw.ruleset.Ruleset(yaml.load(string_))
        yield rule


@_accept_iterable
@_expand_nest_iterable
def load_ftw_rules_from_files(files):
    """ Load a set of yaml files required by ftw
         to a ftw.Ruleset generator

    Arguments:
        files: a set of yaml files required by ftw

    Return a ftw.Ruleset generator
        that will generate all of ftw.Ruleset
         saved in those yaml files
    """
    for file_ in files:
        if os.path.splitext(file_)[-1].lower() != ".yaml":
            raise ValueError(file_ + "is not a .yaml file")
        rules = ftw.util.get_rulesets(file_, False)
        for rule in rules:
            yield rule


@_accept_iterable
@_expand_nest_iterable
def load_ftw_rules_from_directories(directories):
    """ Load a set of directories contains yaml files required
         by ftw to a ftw.Ruleset generator

    Arguments:
        directories: a set of directories contains yaml files
         required by ftw

    Return a ftw.Ruleset generator
        that will generate all of ftw.Ruleset
         saved in those directories
    """
    for directory_ in directories:
        rules = ftw.util.get_rulesets(directory_, True)
        for rule in rules:
            yield rule


@_accept_iterable
@_expand_nest_iterable
def load_ftw_rules_from_paths(paths):
    """ Load a set of paths contains yaml files required by ftw
        to a ftw.Ruleset generator

    Arguments:
        paths: a set of paths contains yaml files required by ftw

    Return a ftw.Ruleset generator
        that will generate all of ftw.Ruleset saved in those paths
    """
    for path_ in paths:
        if os.path.isfile(path_):
            yield load_ftw_rules_from_files(path_)
        elif os.path.isdir(path_):
            yield load_ftw_rules_from_directories(path_)
        else:
            raise IOError("No such file or path: '%s'" % (path_, ))


@_accept_iterable
@_expand_nest_iterable
def load_ftw_tests_from_paths(paths):
    """ Load a set of paths contains yaml files required by ftw
        to a ftw.Test generator

    Arguments:
        paths: a set of paths contains yaml files required by ftw

    Return a ftw.Test generator
        that will generate all of ftw.Test saved in those paths
    """
    for rule in load_ftw_rules_from_paths(paths):
        for test in rule.tests:
            yield test


@_accept_iterable
@_expand_nest_iterable
def load_ftw_stages_from_paths(paths):
    """ Load a set of paths contains yaml files required by ftw
        to a ftw.Stage generator

    Arguments:
        paths: a set of paths contains yaml files required by ftw

    Return a ftw.Stage generator
        that will generate all of ftw.Stage saved in those paths
    """
    for test in load_ftw_tests_from_paths(paths):
        for stage in test.stages:
            yield stage


@_accept_iterable
@_expand_nest_iterable
def load_packets_from_yaml_files(files):
    """ Load a set of yaml files required by ftw
        to a packets generator

    Arguments:
        paths: a set of yaml files required by ftw

    Return a packets generator
        that will generate all of packets saved in those files
    """
    for stage in load_ftw_stages_from_paths(files):
        http_ua = ftw.http.HttpUA()
        http_ua.request_object = stage.input
        http_ua.build_request()
        yield str(http_ua.request)


@_accept_iterable
@_expand_nest_iterable
def load_packets_from_pkt_files(files):
    """Load a set of .pkt files to a packets generator

    Arguments:
        files: a set of files of save packets

    Return a packets generator
    """
    buffer_ = ""
    for file_ in files:
        file_ = os.path.abspath(file_)
        with open(file_, "rb", io.DEFAULT_BUFFER_SIZE) as fd:
            while True:
                bytes_ = fd.read(io.DEFAULT_BUFFER_SIZE)
                if not bytes_:
                    if buffer_:
                        yield buffer_
                    break
                while bytes_:
                    delimit_pos = bytes_.find('\0')
                    if delimit_pos == -1:
                        buffer_ += bytes_
                        bytes_ = None
                    else:
                        buffer_ += bytes_[:delimit_pos]
                        if buffer_:
                            yield buffer_
                        buffer_ = ""
                        bytes_ = bytes_[delimit_pos + 1:]


LOADERS = {
    ".yaml": load_packets_from_yaml_files,
    ".pkt": load_packets_from_pkt_files,
}


@_accept_iterable
@_expand_nest_iterable
def load_packets_from_paths(paths):
    """ Load a set of paths that
        include .pkt or .yaml files to a packets generator.

    Arguments:
        paths: a set of paths include .pkt or .yaml files.

    Return a packets generator
        that will generate all of packets saved in those paths
    """
    for path_ in paths:
        path_ = os.path.abspath(path_)
        if os.path.isdir(path_):
            for root, _, files in os.walk(path_):
                for file_ in files:
                    file_ext = os.path.splitext(file_)[-1].lower()
                    if file_ext not in LOADERS:
                        continue
                    yield LOADERS[file_ext](
                        os.path.join(root, file_))
        elif os.path.isfile(path_):
            file_ext = os.path.splitext(path_)[-1].lower()
            if file_ext not in LOADERS:
                raise ValueError(path_ + " is not supported to load packets")
            yield LOADERS[file_ext](path_)
        else:
            raise IOError("No such file or path: '%s'" % (path_, ))


def execute(paths, exporter=None):
    """ Export all of packets into the exporter

    Arguments:
        paths: a set of paths includes %s files
            or directories contain those kind of files
        exporter: a exporter for receiving packets
    """
    if not isinstance(exporter, packetsexporter.PacketsExporter):
        with packetsexporter.PacketsExporter(exporter) as exporter:
            for packet in load_packets_from_paths(paths):
                exporter.export(packet)
    else:
        for packet in load_packets_from_paths(paths):
            exporter.export(packet)


def _help():
    return '''
loader.py
    load yaml or pkt files into a pkt file

SYNOPSIS
    python loader.py [OPTION] [PATHS...]
    ./loader.py [OPTION] [PATHS...]

DESCRIPTION
    PATHS...        input .yaml/.pkt files or directories that includes \
 these kinds of files
    -o/--output     output packets file , default is stdout
    -h/--help       print help

EXAMPLE
    ./loader.py rtt_ruleset/ -o packets.pkt
    '''


if __name__ == '__main__':
    packets_file = ""
    packets_files = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            print(help())
            sys.exit(0)
        elif sys.argv[i] == "-o" or sys.argv[i] == "--output":
            i += 1
            if i >= len(sys.argv):
                raise ValueError("need an argument as the output")
            packets_file = sys.argv[i]
        else:
            packets_files.append(sys.argv[i])
        i += 1

    execute(packets_files, packets_file)
