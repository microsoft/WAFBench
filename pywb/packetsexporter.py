# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

""" Export packets

This exports:
    - PacketsExporter is a object to export packets into a file
"""

__all__ = ["PacketsExporter"]

import sys


class PacketsExporter(object):
    """ Export packets into a file

    Arguments:
        file_name: A path to save the packets(default = None).

    Attributes:
        file_name: A path to save the packets.
            if file name wasn't set, file name isn't set.

        _file_fd: The file descriptor of file name.
            if file name was None, file_fd is stdout.

        _is_empty: A flag means the file for saving packets is empty
    """
    def __init__(self, file_name=None):
        """ Create a packets exporter
        """
        if file_name:
            self.file_name = file_name
            self._file_fd = open(self.file_name, 'wb')
        else:
            self._file_fd = sys.stdout

        self._is_empty = True

    def export(self, packets):
        """ export packets into the file
        """
        if not hasattr(packets, "__iter__"):
            packets = [packets]
        for packet in packets:
            if not packet:
                continue
            if not self._is_empty:
                self._file_fd.write("\0")
            self._file_fd.write(packet)
            self._is_empty = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self._file_fd != sys.stdout:
            self._file_fd.close()
