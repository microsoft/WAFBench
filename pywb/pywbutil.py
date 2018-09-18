# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Utility of pywb

This exports:
    - get_wb_path is a function to get the path of 'wb'
    - MIME_TYPE_DICT is a dict that save the MIME TYPE
    - accept_iterable is a decorator to make the first argument
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
        ".",
        "../wb/",
    ]
    if "PATH" in os.environ:
        search_positions += os.environ["PATH"].split(":")
    for position in search_positions:
        position = os.path.join(position, "wb")
        if not os.path.isabs(position):
            position = os.path.join(os.path.dirname(__file__), position)
        if os.path.exists(position) and os.path.isfile(position):
            return position
    raise IOError(
        "No executable under such paths: '%s'" % (search_positions, ))


mimetypes.init()  # To load all mime types from system
MIME_TYPE_DICT = mimetypes.types_map  # The dict of MIME TYPE


def accept_iterable(func):
    """ This is a decorator to make the first argument
        of the func to be iterable.

    Because the func only supports an iterator as its first argument,
    this decorator will guarantee that the first argument always is iterable
    make the caller of func can pass a single variable as the first argument
    to the func.
    """
    @functools.wraps(func)
    def _decorator(*args, **kw):
        if hasattr(args[0], "__iter__"):
            iterator = args[0]
        else:
            iterator = [args[0]]
        return func(iterator, *args[1:], **kw)
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
        ret = func(*args, **kw)
        if not isinstance(ret, types.GeneratorType):
            yield ret
        else:
            visitor = ret.__iter__()
            visit_stack = [visitor]
            while visit_stack:
                visitor = visit_stack[-1]
                try:
                    visitor = next(visitor)
                    if isinstance(visitor, types.GeneratorType):
                        visitor = visitor.__iter__()
                        visit_stack.append(visitor)
                    else:
                        yield visitor
                except StopIteration:
                    visit_stack.pop()
    return _decorator
