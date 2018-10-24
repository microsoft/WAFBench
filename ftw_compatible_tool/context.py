#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" context
"""

import traffic


class Context(object):
    def __init__(self, broker, delimiter=traffic.Delimiter()):
        self.delimiter = delimiter
        self.broker = broker
