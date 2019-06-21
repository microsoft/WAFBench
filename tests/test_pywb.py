import BaseHTTPServer
import threading
import time
import os
import base64
import random
import re

from pywb import main

import common


def test_send_packet_specified_number():
    counter = {
        "request" : 0
    }
    class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            counter["request"] += 1
        def do_POST(self):
            self.send_response(200)
            counter["request"] += 1
    with common.HTTPServerInstance(HTTPHandler):
        expect_request_count = 3
        main.execute(["-v", "4", "-n", str(expect_request_count),
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == expect_request_count)

        counter["request"] = 0
        packet_file = os.path.join(os.path.dirname(
            __file__), "data", "big_packet.pkt")
        main.execute(["-v", "4", "-n", "1", "-F",  packet_file,
                      "localhost:" + str(common._PORT)])
        assert(counter["request"] == 1)


def test_send_packet_specified_timelimit():
    with common.HTTPServerInstance():
        expect_request_time = 2
        start_time = time.time()
        main.execute(["-v", "4", "-t", str(expect_request_time),
                    "localhost:" + str(common._PORT)])
        assert(abs((time.time() - start_time) - expect_request_time) < 0.5)


def test_post_file():
    counter = {
        "request" : 0,
    }
    expect_content_type = ""
    class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            assert(self.headers.get("Content-Type") == expect_content_type)
            counter["request"] += 1
    target_file = os.path.join(os.path.dirname(
        __file__), "data", "requestbody2kb.json")
    with common.HTTPServerInstance(HTTPHandler):
        expect_content_type = "wafbench-test"
        main.execute(["-v", "4", "-p", target_file,  "-n", "1", "-T", expect_content_type,
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 1)

        expect_content_type = "application/json"
        main.execute(["-v", "4", "-p", target_file,  "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 2)


def test_header_check():
    counter = {
        "request" : 0,
    }
    expect_header = ()
    class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            if expect_header:
                assert(self.headers.get(expect_header[0]) == expect_header[1])
            counter["request"] += 1
        def do_HEAD(self):
            self.send_response(200)
            counter["request"] += 1

    with common.HTTPServerInstance(HTTPHandler):

        main.execute(["-v", "4", "-i", "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 1)

        expect_header = ("Host", "wafbench")
        main.execute(["-v", "5", "-H", "%s: %s" % expect_header, "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 2)

        expect_header = ("Connection", "wafbench")
        main.execute(["-v", "5", "-H", "%s: %s" % expect_header, "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 3)

        expect_header = ("Cookie", "wafbench=wafbench")
        main.execute(["-v", "5", "-C", expect_header[1], "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 4)

        authorization = "wafbench:wafbench"
        expect_header = ("Authorization", "Basic " +
                        base64.b64encode(authorization))
        main.execute(["-v", "5", "-A", authorization, "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 5)

        authorization = "wafbench:wafbench"
        expect_header = ("Proxy-Authorization", "Basic " +
                        base64.b64encode(authorization))
        main.execute(["-v", "5", "-P", authorization, "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 6)

        expect_header = ("Connection", "Keep-Alive")
        main.execute(["-v", "5", "-k", "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 7)

        expect_header = ("Connection", "Close")
        main.execute(["-v", "5", "-2", "2", "-n", "1",
                    "localhost:" + str(common._PORT)])
        assert(counter["request"] == 8)


def test_response_codes_log():
    candidated_codes = (200, 400, 500)
    response_codes = dict(zip(candidated_codes, [0] * len(candidated_codes)))
    counter = {
        "request" : 0,
    }
    class HTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            code = random.choice(candidated_codes)
            response_codes[code] += 1
            counter["request"] += 1
            self.send_response(code)
    def response_codes_log_collect(line):
        response_code = re.search(r"(\d{3}) response: (\d+)", line)
        if response_code:
            assert(int(response_code.group(2)) == response_codes[int(response_code.group(1))])
    with common.HTTPServerInstance(HTTPHandler):
        main.execute(["-k", "-n", "100",
                      "localhost:" + str(common._PORT)],
                      customized_filters=[response_codes_log_collect])
        counter["request"] = 100;
            

