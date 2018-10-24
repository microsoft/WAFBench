#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" sql
"""

SQL_INITIALIZE_DATABASE = '''
CREATE TABLE Traffic (
    traffic_id TEXT PRIMARY KEY,
    test_title TEXT NOT NULL,
    meta TEXT,
    file TEXT,
    input TEXT,
    output TEXT,
    request BLOB,
    raw_request BLOB,
    raw_response BLOB,
    raw_log TEXT,
    duration_time REAL
);
CREATE INDEX idx_title on Traffic(test_title);
'''

SQL_INSERT_REQUEST = '''
INSERT INTO Traffic (
    traffic_id,
    test_title,
    meta,
    file,
    input,
    output,
    request
    )
    VALUES (
        ?,?,?,?,?,?,?
    );
'''

SQL_QUERY_REQUEST = '''
SELECT traffic_id, request FROM Traffic GROUP BY traffic_id;
'''

SQL_CLEAN_RAW_DATA = '''
UPDATE Traffic
SET raw_request = NULL, raw_response = NULL, raw_log = NULL;
'''

SQL_INSERT_RAW_TRAFFIC = '''
UPDATE Traffic
SET raw_request = ?, raw_response = ?
WHERE traffic_id = ?;
'''

SQL_INSERT_LOG = '''
UPDATE Traffic
SET raw_log = ?
WHERE traffic_id = ?;
'''

SQL_QUERY_RESULT = '''
SELECT
    test_title ,
    output ,
    raw_request ,
    raw_response ,
    raw_log
FROM Traffic;
'''

SQL_QUERY_TEST_TITLE = '''
SELECT test_title
FROM Traffic
WHERE traffic_id = ?;
'''
