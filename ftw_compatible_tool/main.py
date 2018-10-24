#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" ftwcomp(FTW-compatible-Tool)
"""

import argparse
import sys
import ast

import context
import broker
import database
import user_interface
import traffic
import log
import base


def parse(arguments):
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--database", default=":memory:")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("-i", "--interact", action="store_true")
    mode_group.add_argument(
        "-x",
        "--execute",
    )

    arguments = parser.parse_args(arguments)
    return arguments


def execute(arguments, ui=user_interface.CLI, brk=broker.Broker()):

    ctx = context.Context(brk, delimiter=traffic.Delimiter("magic"))

    ui = ui(ctx)

    brk.publish(broker.TOPICS.SHOW_UI, "welcome")
    traffic.RawRequestCollector(ctx)
    traffic.RawResponseCollector(ctx)
    traffic.RealTrafficCollector(ctx)
    log.LogCollector(ctx)
    base.Base(ctx)

    args = parse(arguments)

    database.Sqlite3DB(ctx, args.database)

    if args.interact:
        brk.publish(broker.TOPICS.SHOW_UI, "tutorial")
        ui.interact()
    else:
        commands = args.execute.decode("string_escape").strip().splitlines()
        for command in commands:
            brk.publish(broker.TOPICS.COMMAND,
                        *tuple(command.strip().split(' ')))


if __name__ == "__main__":
    execute(sys.argv[1:])
    import gc
