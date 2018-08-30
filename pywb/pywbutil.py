# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Utility of pywb

This exports:
    - get_wb_path is a function to get the path of 'wb'
    - MIME_TYPE_DICT is a dict that save the MIME TYPE
"""

__all__ = [
    "get_wb_path",
    "MIME_TYPE_DICT",
]

import os
import sys
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
