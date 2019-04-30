#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
""" testdata, created for ftw_compatible_tool's test.

If you are using ftw_compatible_tool, you must have no need to use this module.
"""

TEST_PYWB_OUTPUT = '''
WAF-Bench(wb) Version 1.2.1(Build: Aug 31 2018 14:26:32).
  By Networking Research Group of Microsoft Research, 2018.
wb is based on ApacheBench, Version 2.3 <1818629>

Benchmarking localhost (be patient)...
INFO: GET header ==
---
GET / HTTP/1.0
Host: Localhost
Connection: Close
User-Agent: ApacheBench/2.3
Accept: */*


---

 read 6 packets from file with total length(745).

writing request(161 bytes)=>[GET / HTTP/1.1\r
Host: 334787923864975794240893756898805143302-<334787923944203956755158094492349093638>\r
Accept: */*\r
User-Agent: WAFBench\r
Connection: Close\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.2\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
writing request(86 bytes)=>[GET /index.html HTTP/1.1\r
Host: localhost\r
Connection: close\r
User-Agent: WAFBench\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.6\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
writing request(161 bytes)=>[GET / HTTP/1.1\r
Host: 334787923864975794240893756898805143302-<334787923944203956755158094492349093638>\r
Accept: */*\r
User-Agent: WAFBench\r
Connection: Close\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.7\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
writing request(161 bytes)=>[GET / HTTP/1.1\r
Host: 334787923864975794240893756898805143302-<334787924023432119269422432085893043974>\r
Accept: */*\r
User-Agent: WAFBench\r
Connection: Close\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.8\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
writing request(86 bytes)=>[GET /index.html HTTP/1.1\r
Host: localhost\r
Connection: close\r
User-Agent: WAFBench\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.9\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
writing request(161 bytes)=>[GET / HTTP/1.1\r
Host: 334787923864975794240893756898805143302-<334787924023432119269422432085893043974>\r
Accept: */*\r
User-Agent: WAFBench\r
Connection: Close\r
\r
]
LOG: http packet received(711 bytes):
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.1\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

LOG: header received:
HTTP/1.1 502 Bad Gateway\r
Server: nginx/1.11.5\r
Date: Mon, 22 Oct 2018 06:30:35 GMT\r
Content-Type: text/html\r
Content-Length: 537\r
Connection: close\r
ETag: "5ac31fd1-219"\r
\r
<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>An error occurred.</h1>
<p>Sorry, the page you are looking for is currently unavailable.<br/>
Please try again later.</p>
<p>If you are the system administrator of this resource then you should check
the <a href="http://nginx.org/r/error_log">error log</a> for details.</p>
<p><em>Faithfully yours, nginx.</em></p>
</body>
</html>

WARNING: Response code not 2xx (502)
 1: Completed      6 requests, rate is 1877 #/sec.
Finished 6 requests

Server Software:        nginx/1.11.5
Server Hostname:        localhost
Server Port:            18080

Document Path:          /
Document Length:        Variable

Concurrency Level:      1
Time taken for tests:   0.003 seconds
Complete requests:      6
Failed requests:        0
Non-2xx responses:      6
Total transferred:      4266 bytes
HTML transferred:       3222 bytes
Requests per second:    1852.42 [#/sec] (mean)
Time per request:       0.540 [ms] (mean)
Transfer rate:          1286.20 [Kbytes/sec] received
Total samples of stats: 6
Connection Times (us)
              min  mean[+/-sd] median   max
Connect:       52   68  12.8     74      82
Processing:   366  436  49.6    442     510
Waiting:      229  312  63.4    323     406
Total:        448  504  50.3    494     589

Percentage of the requests served within a certain time (us)
  50%    494
  66%    494
  75%    536
  80%    536
  90%    589
  95%    589
  98%    589
  99%    589
 100%    589 (longest request)
    '''

TEST_MODSECURITY_LOG = '''
2018/10/22 17:41:36 [error] 3439#3439: *1 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:28080/", host: "334787923864975794240893756898805143302-<245154438456484133445805079042224150278>"
2018/10/22 17:41:36 [error] 3439#3439: [client 127.0.0.1] ModSecurity: Warning. Pattern match "334787923864975794240893756898805143302-<(\\w*)>" at REQUEST_HEADERS:Host. [file "/home/ganze/testbed/default-nginx-1.11.5-ModSecurity-original/conf/my_modsecurity_conf/default.conf"] [line "31"] [id "010203"] [msg "334787923864975794240893756898805143302-<245154438456484133445805079042224150278>"] [hostname ""] [uri "/"] [unique_id "AcPcAcAcA0APAcAcAcAcAcAc"]
2018/10/22 17:41:36 [error] 3439#3439: *3 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET /index.html HTTP/1.1", upstream: "http://127.0.0.1:28080/index.html",
host: "localhost"
2018/10/22 17:41:36 [error] 3439#3439: *5 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:28080/", host: "334787923864975794240893756898805143302-<245154438456484133445805079042224150278>"
2018/10/22 17:41:36 [error] 3439#3439: [client 127.0.0.1] ModSecurity: Warning. Pattern match "334787923864975794240893756898805143302-<(\\w*)>" at REQUEST_HEADERS:Host. [file "/home/ganze/testbed/default-nginx-1.11.5-ModSecurity-original/conf/my_modsecurity_conf/default.conf"] [line "31"] [id "010203"] [msg "334787923864975794240893756898805143302-<245154438456484133445805079042224150278>"] [hostname ""] [uri "/"] [unique_id "A5AcAcAcAVAlttqcAcAcAcAc"]
2018/10/22 17:41:36 [error] 3439#3439: *7 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:28080/", host: "334787923864975794240893756898805143302-<245154438535712295960069416635768100614>"
2018/10/22 17:41:36 [error] 3439#3439: [client 127.0.0.1] ModSecurity: Warning. Pattern match "334787923864975794240893756898805143302-<(\\w*)>" at REQUEST_HEADERS:Host. [file "/home/ganze/testbed/default-nginx-1.11.5-ModSecurity-original/conf/my_modsecurity_conf/default.conf"] [line "31"] [id "010203"] [msg "334787923864975794240893756898805143302-<245154438535712295960069416635768100614>"] [hostname ""] [uri "/"] [unique_id "AcAcAcAcAcwbAnucAcAcAcAc"]
2018/10/22 17:41:36 [error] 3439#3439: *9 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET /index.html HTTP/1.1", upstream: "http://127.0.0.1:28080/index.html",
host: "localhost"
2018/10/22 17:41:36 [error] 3439#3439: *11 connect() failed (111: Connection refused) while connecting to upstream, client: 127.0.0.1, server: localhost, request: "GET / HTTP/1.1", upstream: "http://127.0.0.1:28080/", host: "334787923864975794240893756898805143302-<245154438535712295960069416635768100614>"
2018/10/22 17:41:36 [error] 3439#3439: [client 127.0.0.1] ModSecurity: Warning. Pattern match "334787923864975794240893756898805143302-<(\\w*)>" at REQUEST_HEADERS:Host. [file "/home/ganze/testbed/default-nginx-1.11.5-ModSecurity-original/conf/my_modsecurity_conf/default.conf"] [line "31"] [id "010203"] [msg "334787923864975794240893756898805143302-<245154438535712295960069416635768100614>"] [hostname ""] [uri "/"] [unique_id "AcAcecAZAcqcAcAcXdAFlcAG"]
'''

TEST_SHOW_DATABASE = '''
SELECT * FROM Traffic;
'''


def PrintQueryResult(result):
    print(result.title())
    for row in result:
        print(row)


def PrintMessage(*args, **kwargs):
    print(repr(args))
    print(repr(kwargs))
