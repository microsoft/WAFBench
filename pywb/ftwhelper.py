# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" FTW helper

This export:
    - FTW_TYPE: is a enum that contains RULE, TEST, STAGE, PACKETS.
    - FtwDict: is a subclass of dict, that store the data from ftw
    - FtwStr: is a subclass of str, that store the data from ftw
    - get: is a function to get a target_type generator from sources.

This is a wrapper to provied the access to FTW(https://github.com/fastly/ftw).
"""

import os
import enum
import yaml
import types

import ftw

import pywbutil

__all__ = [
    "FTW_TYPE",
    "FtwDict",
    "FtwStr",
    "get",
]


class FTW_TYPE(enum.IntEnum):
    """ FTW_TYPE
        RULE is a FtwDict
        TEST is a FtwDict
        STAGE is a FtwDict
        PACKETS is a FtwStr
    """
    RULE = 0
    TEST = 1
    STAGE = 2
    PACKETS = 3
    INVALID = 4


class FtwDict(dict):
    """ Store the data from ftw """
    def __init__(self, *args, **kw):
        super(FtwDict, self).__init__(*args, **kw)
        self.FTW_TYPE = FTW_TYPE.INVALID
        self.ORIGIN_FILE = None
        self.ORIGIN_DATA = None


class FtwStr(str):
    """ Store the data from ftw """
    def __init__(self, content):
        super(FtwStr, self).__init__(content)
        self.FTW_TYPE = FTW_TYPE.INVALID
        self.ORIGIN_FILE = None
        self.ORIGIN_DATA = None


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_strings(strings):
    for string_ in strings:
        ftw_rule = ftw.ruleset.Ruleset(yaml.load(string_))
        rule = FtwDict(ftw_rule.yaml_file)
        rule.ORIGIN_DATA = ftw_rule
        rule.FTW_TYPE = FTW_TYPE.RULE
        yield rule


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_files(files):
    for file_ in files:
        if os.path.splitext(file_)[-1].lower() != ".yaml":
            raise ValueError(file_ + "is not a .yaml file")
        rules = ftw.util.get_rulesets(file_, False)
        for ftw_rule in rules:
            rule = FtwDict(ftw_rule.yaml_file)
            rule.ORIGIN_DATA = ftw_rule
            rule.ORIGIN_FILE = file_
            rule.FTW_TYPE = FTW_TYPE.RULE
            yield rule


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_paths(paths):
    for path_ in paths:
        path_ = os.path.abspath(path_)
        if os.path.isdir(path_):
            for root, _, files in os.walk(path_):
                for file_ in files:
                    file_ext = os.path.splitext(file_)[-1].lower()
                    if file_ext != ".yaml":
                        continue
                    yield _load_ftw_rules_from_files(
                        os.path.join(root, file_))
        elif os.path.isfile(path_):
            file_ext = os.path.splitext(path_)[-1].lower()
            if file_ext != ".yaml":
                raise ValueError(path_ + " is not YAML file with .yaml")
            yield _load_ftw_rules_from_files((path_))
        else:
            raise IOError("No such file or path: '%s'" % (path_, ))


def _convert(source, target_type):
    if not hasattr(source, "FTW_TYPE") \
            or source.FTW_TYPE == FTW_TYPE.INVALID \
            or target_type == FTW_TYPE.INVALID:
        raise ValueError("%s is invalid type" % (source, ))
    if source.FTW_TYPE > FTW_TYPE:
        raise ValueError(
            "Cannot do this upper convert from %s to %s"
            % (source.FTW_TYPE, FTW_TYPE))

    if source.FTW_TYPE == FTW_TYPE:
        yield source
    # ftw.stage => pkt
    elif source.FTW_TYPE == FTW_TYPE.STAGE \
            and target_type == FTW_TYPE.PACKETS:
        http_ua = ftw.http.HttpUA()
        http_ua.request_object = source.ORIGIN_DATA.input
        http_ua.build_request()
        packet = FtwStr(http_ua.request)
        packet.FTW_TYPE = FTW_TYPE.PACKETS
        packet.ORIGIN_DATA = http_ua.request
        packet.ORIGIN_FILE = source.ORIGIN_FILE
        yield packet
    # ftw.test => ftw.stage
    elif source.FTW_TYPE == FTW_TYPE.TEST \
            and target_type == FTW_TYPE.STAGE:
        for ftw_stage in source.ORIGIN_DATA.stages:
            stage = FtwDict(ftw_stage.stage_dict)
            stage.FTW_TYPE = FTW_TYPE.STAGE
            stage.ORIGIN_DATA = ftw_stage
            stage.ORIGIN_FILE = source.ORIGIN_FILE
            yield stage
    # ftw.rule => ftw.test
    elif source.FTW_TYPE == FTW_TYPE.RULE \
            and target_type == FTW_TYPE.TEST:
        for ftw_test in source.ORIGIN_DATA.tests:
            test = FtwDict(ftw_test.test_dict)
            test.FTW_TYPE = FTW_TYPE.TEST
            test.ORIGIN_DATA = ftw_test
            test.ORIGIN_FILE = source.ORIGIN_FILE
            yield test
    # ftw.* => ftw.*
    else:
        internal_type = source.FTW_TYPE + 1
        source = _convert(source, internal_type)
        visitor = source.__iter__()
        visit_stack = [visitor]
        while visit_stack:
            visitor = visit_stack[-1]
            try:
                visitor = next(visitor)
                if visitor.FTW_TYPE < target_type:
                    visitor = _convert(visitor, visitor.FTW_TYPE + 1)
                    visit_stack.append(visitor)
                else:
                    yield visitor
            except StopIteration:
                visit_stack.pop()


def get(source, target_type):
    """ Get a target_type generator from sources.

    Arguments:
        source:
            a set of paths with YAML extension to ftw
            and string with YAML format to ftw
            or
            objects that comes from ftwhelper.get
        target_type: a enum of FTW_TYPE to specify the generator type

    Return a generator that generate target_type
    """
    if hasattr(source, "FTW_TYPE"):
        for item in _convert(source, target_type):
            yield item
    else:
        if not hasattr(source, "__iter__"):
            sources = [source]
        else:
            sources = source
        for source in sources:
            if os.path.exists(source):
                rules = _load_ftw_rules_from_paths(source)
            else:
                rules = _load_ftw_rules_from_strings(source)
            for rule in rules:
                for destination in _convert(rule, target_type):
                    yield destination
