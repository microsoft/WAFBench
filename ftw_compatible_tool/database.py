#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" database

This exports:
    - QueryResult is a class that stores result of one database query.
    - Database is an abstract class that delcares database's interface,
        and implements interactions with broker.
    - Sqlite3DB is a class inherited from Database
        that uses SQLite3 as its database type.
"""

import sqlite3
import abc

import sql
import context
import broker


class QueryResult(object):
    """ Stores result of one database query.

    Arguments:
        - rows: A list. Each element is a row in database.
        - row_count: The number of valid elements in rows.
        - title: Row's title in database.

    Attributes:
        Same as Arguments.
    """
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
    """ Database's ABC.

    Arguments:
        - context: A Context object.

    Attributes:
        Same as Arguments.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, context):
        """ Create a Database,
            subscribe itself to SQL_QUERY,
            query for initializing database.
        """
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
        """ Query database by script with args.

        Arguments:
            - script: A database query.
            - args: Query's arguments.

        Return is a QueryResult object saving query result.
        """
        return QueryResult()

    def _query(self, script, *args, **kwargs):
        result = self.query(script, *args)
        if "callback" in kwargs:
            kwargs["callback"](result)


class Sqlite3DB(Database):
    """ Database using SQLite3 as its kernel.

    Arguments:
        - context: A Context object.
        - path: Database's path(default is in memory).

    Attributes:
        - _connector: A sqlite3.Connection object.
    """
    def __init__(self, context, path=":memory:"):
        """ Create a Sqlite3DB object,
            connect to the database in path,
            call Database's initializing.
        """
        self._connector = sqlite3.connect(path)
        self._connector.text_factory = str
        super(Sqlite3DB, self).__init__(context)

    def query(self, script, *args):
        """ See Database.query.

        Arguments:
            - script: A string meaning a SQLite3 query.
            - args: Query's arguments.

        Return see Database.query.
        """
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
