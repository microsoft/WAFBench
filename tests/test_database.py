import collections

from ftw_compatible_tool import database
from ftw_compatible_tool import sql
from ftw_compatible_tool import context
from ftw_compatible_tool import broker


_SQL_GET_ALL_DATA = "SELECT * from Traffic;"


def test_database_create():
    ctx = context.Context(broker.Broker())
    db = database.Sqlite3DB(ctx)
    r = db.query(_SQL_GET_ALL_DATA)
    expect_titles = ("traffic_id", "test_title",
                    "meta", "file",
                    "input", "output",
                    "request", "raw_request",
                    "raw_response", "raw_log",
                    "testing_result", "duration_time")
    assert(len(expect_titles) == len(r.title()))
    for title in expect_titles:
        assert(title in r.title())


def check_insert(db, args):
    count = 0
    for r in db.query(_SQL_GET_ALL_DATA):
        count += 1
        for arg in args:
            assert(arg in r)
    return count

def test_sql():
    ctx = context.Context(broker.Broker())
    db = database.Sqlite3DB(ctx)

    # insert request
    args = ("id_1", "test_title", "meta_data", "file_path",
            "input_data", "output_data", "request_data")
    db.query(sql.SQL_INSERT_REQUEST, *args)
    check_insert(db, args)

    # query request   
    result = db.query(sql.SQL_QUERY_REQUEST)
    data = collections.OrderedDict(zip(result.title(), next(iter(result))))
    assert(len(data) == 2)
    assert(data["traffic_id"] == "id_1")
    assert(data["request"] == "request_data")

    # insert raw traffic
    args = ("raw_request", "raw_response", "duration_time", "id_1")
    db.query(sql.SQL_INSERT_RAW_TRAFFIC, *args)
    check_insert(db, args)

    # insert raw log
    args = ("raw_log", "id_1")
    db.query(sql.SQL_INSERT_LOG, *args)
    check_insert(db, args)

    # insert raw log
    args = ("True", "id_1")
    db.query(sql.SQL_UPDATE_TESTING_RESULT, *args)
    check_insert(db, args)

    # query result
    result = db.query(sql.SQL_QUERY_RESULT)
    data = collections.OrderedDict(zip(result.title(), next(iter(result))))
    assert(len(data) == 6)
    assert(data["traffic_id"] == "id_1")
    assert(data["test_title"] == "test_title")
    assert(data["output"] == "output_data")
    assert(data["raw_request"] == "raw_request")
    assert(data["raw_response"] == "raw_response")
    assert(data["raw_log"] == "raw_log")

    # clean raw data
    db.query(sql.SQL_CLEAN_RAW_DATA)
    result = db.query(_SQL_GET_ALL_DATA)
    data = collections.OrderedDict(zip(result.title(), next(iter(result))))
    assert(data["raw_request"] == None)
    assert(data["raw_response"] == None)
    assert(data["raw_log"] == None)
    assert(data["testing_result"] == None)


