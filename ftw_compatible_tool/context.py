#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" context

This exports:
    - Context is a class shared by all components in ftw_compatible_tool.
"""

import traffic


class Context(object):
    """ Store data or objects shared by all components.
    
    Arguments:
        - broker: A Broker object.
        - delimiter: A Delimiter object.

    Attributes:
        Same as Arguments.
    """
    def __init__(self, broker, delimiter=traffic.Delimiter()):
        self.delimiter = delimiter
        self.broker = broker
