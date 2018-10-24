#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" log
"""

import collector
import context
import sql
import broker
import traffic


class LogCollector(collector.SwitchCollector):
    def __init__(self, ctx):
        self._ctx = ctx
        super(LogCollector, self).__init__(
            self._ctx.delimiter.get_delimiter_log(),
            self._ctx.delimiter.get_delimiter_log())
        self._reset()

        self._ctx.broker.subscribe(broker.TOPICS.RAW_LOG, self)
        self._ctx.broker.subscribe(broker.TOPICS.RESET, self._reset)

    def __del__(self):
        self._ctx.broker.unsubscribe(broker.TOPICS.RAW_LOG, self)
        self._ctx.broker.subscribe(broker.TOPICS.RESET, self._reset)

    def _execute(self, collected_buffer, start_result, end_result):
        key = start_result.group(1)
        if key != end_result.group(1):
            return
        # remove delimiter
        collected_buffer = collected_buffer.splitlines()
        if len(collected_buffer) < 2:
            self._ctx.broker.publish(broker.TOPICS.WARNING, "log error")
            return
        log_buffer = "\n".join(collected_buffer[1:-1])
        self._ctx.broker.publish(
            broker.TOPICS.SQL_QUERY,
            sql.SQL_INSERT_LOG,
            log_buffer,
            key,
        )


if __name__ == "__main__":
    import testdata

    ctx = context.Context(
        broker.Broker(),
        delimiter=traffic.Delimiter("334787923864975794240893756898805143302"))
    log_collector = LogCollector(ctx)
    ctx.broker.subscribe(broker.TOPICS.SQL_QUERY, testdata.PrintMessage)

    for line in testdata.TEST_MODSECURITY_LOG.splitlines():
        ctx.broker.publish(broker.TOPICS.RAW_LOG, line + "\n")
