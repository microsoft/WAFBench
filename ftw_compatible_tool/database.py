#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" database
"""

import sqlite3
import abc

import sql
import context
import broker


class QueryResult(object):
    def __init__(self, rows=[], row_count=0, title=None):
        self._rows = rows
        self._row_count = row_count
        self._title = title

    def __iter__(self):
        for row in self._rows:
            yield row

    def row_count(self):
        return self._row_count

    def title(self):
        return self._title


class Database(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, context):
        self.context = context
        self.context.broker.subscribe(broker.TOPICS.SQL_QUERY, self._query)
        try:
            self.query(sql.SQL_INITIALIZE_DATABASE)
        except sqlite3.OperationalError:
            # ignore repeatedly initialize error
            pass

    def __del__(self):
        self.context.broker.unsubscribe(broker.TOPICS.SQL_QUERY, self._query)

    @abc.abstractmethod
    def query(self, script, *args):
        return QueryResult()

    def _query(self, script, *args, **kwargs):
        result = self.query(script, *args)
        if "callback" in kwargs:
            kwargs["callback"](result)


class Sqlite3DB(Database):
    def __init__(self, context, path=":memory:"):
        self._connector = sqlite3.connect(path)
        self._connector.text_factory = str
        super(Sqlite3DB, self).__init__(context)

    def query(self, script, *args):
        cursor = self._connector.cursor()
        try:
            cursor.execute(script, args)
        except sqlite3.Warning:
            cursor.executescript(script)
        finally:
            self._connector.commit()

        def row_gen(cursor):
            row = cursor.fetchone()
            while row:
                yield row
                row = cursor.fetchone()

        row_count = cursor.rowcount
        if cursor.description:
            title = tuple(map(lambda column: column[0], cursor.description))
        else:
            title = tuple()
        return QueryResult(row_gen(cursor), row_count, title)


if __name__ == "__main__":
    context = context.Context(broker.Broker())

    db = Sqlite3DB(context)
    context.broker.publish(
        broker.TOPICS.SQL_QUERY,
        sql.SQL_INSERT_REQUEST,
        "id_1",
        "test_title",
        "meta_data",
        "file_path",
        "input_data",
        "output_data",
        "request_data",
    )
    context.broker.publish(
        broker.TOPICS.SQL_QUERY,
        sql.SQL_INSERT_RAW_TRAFFIC,
        "raw_request_data",
        "raw_response_data",
        "id_1",
    )
    context.broker.publish(
        broker.TOPICS.SQL_QUERY,
        sql.SQL_INSERT_LOG,
        "log_data",
        "id_1",
    )

    def print_result(result):
        print(result.title())
        for row in result:
            print(row)

    print_result(db.query("select * from Traffic;"))
    context.broker.publish(
        broker.TOPICS.SQL_QUERY,
        "select * from Traffic;",
        callback=print_result)
