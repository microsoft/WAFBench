# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Utility of pywb

This exports:
    - get_wb_path is a function to get the path of 'wb'
    - MIME_TYPE_DICT is a dict that save the MIME TYPE
    - accept_iterable is a decorator to make the argument
        of the func to be iterable.
    - expand_nest_generator is a decorator to
        recursively expand the return values of the func,
        if the return values is generators.
"""

__all__ = [
    "get_wb_path",
    "MIME_TYPE_DICT",
    "accept_iterable",
    "expand_nest_generator",
]

import os
import sys
import functools
import types
import mimetypes


def get_wb_path():
    """ Get the path of 'wb'
    """
    search_positions = [
        "./wb",
        "../wb/wb",
        "/bin/wb",
        "/usr/bin/wb",
    ]
    for position in search_positions:
        if not os.path.isabs(position):
            position = os.path.join(os.path.dirname(__file__), position)
        if os.path.exists(position) and os.path.isfile(position):
            print position
            return position
    raise IOError("wb cannot be found")


mimetypes.init()  # To load all mime types from system
MIME_TYPE_DICT = mimetypes.types_map  # The dict of MIME TYPE


def accept_iterable(func):
    """ This is a decorator to make the argument of the func to be iterable """
    @functools.wraps(func)
    def _decorator(iterable_, *args, **kw):
        if not hasattr(iterable_, "__iter__"):
            iterable_ = [iterable_]
        return func(iterable_, *args, **kw)
    return _decorator


def expand_nest_generator(func):
    """ This is a decorator to recursively expand the return values of the func,
        if the return values is generators.

    If the return values of func is an generator or the generator
    can generate other generators, this decorator will expand
    all generators util objects aren't generators.
    """
    @functools.wraps(func)
    def _decorator(*args, **kw):
        iterable_ = func(*args, **kw)
        if not isinstance(iterable_, types.GeneratorType):
            yield iterable_
        else:
            iterable_ = iterable_.__iter__()
            visit_stack = [iterable_]
            while visit_stack:
                iterable_ = visit_stack[-1]
                try:
                    iterable_ = next(iterable_)
                    if isinstance(iterable_, types.GeneratorType):
                        iterable_ = iterable_.__iter__()
                        visit_stack.append(iterable_)
                    else:
                        yield iterable_
                except StopIteration:
                    visit_stack.pop()
    return _decorator