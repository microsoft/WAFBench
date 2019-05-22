from ftw_compatible_tool import traffic
from ftw_compatible_tool import broker
from ftw_compatible_tool import context
import re


_TEST_PYWB_OUTPUT = '''
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
Host: magic-334787923944203956755158094492349093638\r
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
Host: magic-334787923944203956755158094492349093638\r
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
Host: magic-334787924023432119269422432085893043974\r
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
Host: magic-334787924023432119269422432085893043974\r
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

def test_traffic_extract():
    request_buffer = []
    response_buffer = []
    traffic_buffer = []
    def get_request(request):
        request_buffer.append(request)
    def get_response(response):
        response_buffer.append(response)
    def get_traffic(sql, request, response, duration, id):
        assert(re.search(r"^GET", request) is not None)
        assert(re.search(r"^HTTP", response) is not None)
        assert(re.search(r"^\d+.\d+$", str(duration)) is not None)
        assert(re.search(r"^\d+$", id) is not None)
        traffic_buffer.append((request, response))

    ctx = context.Context(broker.Broker(), traffic.Delimiter("magic"))
    ctx.broker.subscribe(broker.TOPICS.RAW_REQUEST, get_request)
    ctx.broker.subscribe(broker.TOPICS.RAW_RESPONSE, get_response)
    ctx.broker.subscribe(broker.TOPICS.SQL_COMMAND, get_traffic)

    traffic.RawRequestCollector(ctx)
    traffic.RawResponseCollector(ctx)
    traffic.RealTrafficCollector(ctx)

    for line in _TEST_PYWB_OUTPUT.splitlines():
        ctx.broker.publish(broker.TOPICS.PYWB_OUTPUT, line + "\n")

    assert(len(request_buffer) == 6)
    assert(len(response_buffer) == 6)
    assert(len(traffic_buffer) == 2)
    for t in traffic_buffer:
        assert(t[0] in request_buffer and t[1] in response_buffer)
