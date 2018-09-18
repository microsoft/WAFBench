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


class FTW_TYPE(object):
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
    """ Store the data from ftw

    Argument:
        - ftw_type: a value of FTW_TYPE.
        - original_file: a string of path to specified
            where this dict come from
        - original_data: an internal type of ftw.
        - *args, **kw: arguments to initialize a dict.
            It's the dict format of original data.
    """
    def __new__(cls, ftw_type, original_file, original_data, *args, **kw):
        obj = dict.__new__(cls, *args, **kw)
        return obj

    def __init__(self, ftw_type, original_file, original_data, *args, **kw):
        self.update(*args, **kw)
        self.FTW_TYPE = ftw_type
        self.ORIGINAL_FILE = original_file
        self.ORIGINAL_DATA = original_data


class FtwStr(str):
    """ Store the data from ftw

    Argument:
        - ftw_type: a value of FTW_TYPE.
        - original_file: a string of path to specified
            where this dict come from
        - original_data: an string.
    """
    def __new__(cls, ftw_type, original_file, original_data):
        obj = str.__new__(cls, original_data)
        return obj

    def __init__(self, ftw_type, original_file, original_data):
        self.FTW_TYPE = ftw_type
        self.ORIGINAL_FILE = original_file


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_strings(strings):
    for string_ in strings:
        ftw_rule = ftw.ruleset.Ruleset(yaml.load(string_))
        rule = FtwDict(
            FTW_TYPE.RULE,
            None,
            ftw_rule,
            ftw_rule.yaml_file)
        yield rule


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_files(files):
    for file_ in files:
        file_ = os.path.abspath(os.path.expanduser(file_))
        if os.path.splitext(file_)[-1].lower() != ".yaml":
            raise ValueError(file_ + "is not a .yaml file")
        rules = ftw.util.get_rulesets(file_, False)
        for ftw_rule in rules:
            rule = FtwDict(
                FTW_TYPE.RULE,
                file_,
                ftw_rule,
                ftw_rule.yaml_file)
            yield rule


@pywbutil.accept_iterable
@pywbutil.expand_nest_generator
def _load_ftw_rules_from_paths(paths):
    for path_ in paths:
        path_ = os.path.abspath(os.path.expanduser(path_))
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
        http_ua.request_object = source.ORIGINAL_DATA.input
        http_ua.build_request()
        packet = FtwStr(
            FTW_TYPE.PACKETS,
            source.ORIGINAL_FILE,
            http_ua.request)
        yield packet
    # ftw.test => ftw.stage
    elif source.FTW_TYPE == FTW_TYPE.TEST \
            and target_type == FTW_TYPE.STAGE:
        for ftw_stage in source.ORIGINAL_DATA.stages:
            stage = FtwDict(
                FTW_TYPE.STAGE,
                source.ORIGINAL_FILE,
                ftw_stage,
                ftw_stage.stage_dict)
            yield stage
    # ftw.rule => ftw.test
    elif source.FTW_TYPE == FTW_TYPE.RULE \
            and target_type == FTW_TYPE.TEST:
        for ftw_test in source.ORIGINAL_DATA.tests:
            test = FtwDict(
                FTW_TYPE.TEST,
                source.ORIGINAL_FILE,
                ftw_test,
                ftw_test.test_dict)
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
            path_ = os.path.abspath(os.path.expanduser(source))
            if os.path.exists(path_):
                rules = _load_ftw_rules_from_paths(path_)
            else:
                rules = _load_ftw_rules_from_strings(source)
            for rule in rules:
                for destination in _convert(rule, target_type):
                    yield destination
