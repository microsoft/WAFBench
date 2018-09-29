# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Load multiple packets into a packets generator

This exports:
    - LOADERS: is a dict, the key is file extension of supported files
        of loader. the value is the load function that create
        a packets generator from file.
    - load_packets_from_paths: is a function that load a set of paths
        that include .pkt or .yaml files to a packets generator.

Load packets saved in files(.yaml, .pkt) or strings into a packets generator
"""

__all__ = [
    "LOADERS",
    "load_packets_from_paths",
]

import os
import io
import sys
import functools

import ftw
import yaml

import pywbutil
import ftwhelper


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_packets_from_yaml_files(files):
    yield ftwhelper.get(files, ftwhelper.FTW_TYPE.PACKETS)


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_packets_from_pkt_files(files):
    buffer_ = ""
    for file_ in files:
        file_ = os.path.abspath(os.path.expanduser(file_))
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
    ".yaml": _load_packets_from_yaml_files,
    ".pkt": _load_packets_from_pkt_files,
}


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def load_packets_from_paths(paths):
    """ Load a set of paths that
        include .pkt or .yaml files to a packets generator.

    Arguments:
        paths: a set of paths include .pkt or .yaml files.

    Return a packets generator
        that will generate all of packets saved in those paths
    """
    for path_ in paths:
        path_ = os.path.abspath(os.path.expanduser(path_))
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

