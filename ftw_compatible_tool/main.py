#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" ftwcomp(FTW-compatible-Tool)

This exports:
    - parse is a function that parse cmdline's args
    - execute is a function that executes ftw_compatible_tool
"""

__all__ = [
    "parse",
    "execute"
]

import argparse
import sys
import ast
import shlex
import os

sys.path.append(
    os.path.realpath(
        os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            os.pardir
        )
    )
)


import context
import broker
import database
import user_interface
import traffic
import log
import base


def parse(arguments):
    """ Parse cmdline's args into a struct.

    Arguments:
        - arguments: A string list of cmdline's args.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--database",
        default=":memory:",
        help='''
        You can specify a database file to store or restore your testing procedure.
        If this argument wasn't provied the memory database wil be used, which means
        the procedure will not be perserved.
        ''')

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "-i",
        "--interact",
        action="store_true",
        help = '''
        You can use a interact mode to use this program.
        '''
    )
    mode_group.add_argument(
        "-x",
        "--execute",
        help = '''
        You can use a batch mode to use this program, each internal commands seperated by '|'.
        e.g. -x 'load ~/testcases | gen | start targetserver | report'
        '''
    )

    arguments = parser.parse_args(arguments)
    return arguments


def execute(arguments, ui=user_interface.CLI, brk=broker.Broker()):
    """ Execute ftw_compatible_tool.

    Arguments:
        - arguments: A string list fo the arguments for pywb.
        - ui: A class inherited from user_interface.Interactor.
            This will be used for output and interaction.
        - brk: A Broker object.
            Pass this into execute if you have your own subscriber or publisher.
    """

    ctx = context.Context(brk, delimiter=traffic.Delimiter("magic"))

    ui = ui(ctx)

    brk.publish(broker.TOPICS.SHOW_UI, "welcome")
    brk.publish(broker.TOPICS.SHOW_UI, "tutorial")
    traffic.RawRequestCollector(ctx)
    traffic.RawResponseCollector(ctx)
    traffic.RealTrafficCollector(ctx)
    log.LogCollector(ctx)
    base.Base(ctx)

    args = parse(arguments)

    database.Sqlite3DB(ctx, args.database)

    if args.interact:
        ui.interact()
    else:
        commands = args.execute.strip().split("|")
        for command in commands:
            brk.publish(broker.TOPICS.COMMAND,
                        *tuple(shlex.split(command)))


if __name__ == "__main__":
    execute(sys.argv[1:])
