# WAF-Bench (wb): a benchmarking tool for Web Application Firewall (WAF)

wb is based on the latest ApacheBench (ab) and add several new features for WAF testing. 

wb is ab's superset, so its behavior is not changed if no WAF specific feature is used.

## Summary

wb is a tool for benchmarking your Apache Hypertext Transfer Protocol (HTTP) server. It is designed to give you an impression of how your current Apache installation performs. This especially shows you how many requests per second your Apache installation is capable of serving.

wb has some new features:

1. wb can read single or multiple packets file, with -F option.
2. wb can set duration (-t) exactly, no implicit limit of 50K requests.
3. wb also removes implicit limitation of # of requests during test. That’s only used for per-request stats in previous ab tool
4. wb can print out progress every 1 second (modify interval using -j)
5. wb can save received http header to output file (-o). Use -K to save body as well, otherwise only save header
6. wb will automatically add "localhost, close" header fields if absent. You can use -1/-2 to disable such feature.
7. wb uses a pkt_array to store pkt data pointers, by default we save all packets in packets file, but you can use -Q to limit # of pkt in file.
8. wb can limit the output file size, using -G option (default unlimited). Once it exceeds such limit, wb will rewind the file to the beginning.
9. Output results can use micro-second granularity by option "-3". We keep using an array to do stats, but we decouple the array with the number of requests. We always sample the last "-W stats_num" request during the test, and you can configure that value (default is 50,000).
10. wb can also add a message seq# to the header. To do this, you can:
    * use -U option to specify a fixed prefix to each URL, or you can:
    * use -J <sub_string> to specify the string to be substitued in header.
    
    For example, to add a prefix "YAML_TEST_[SEQ_ID]" to URL like this:

    ```
    GET /YAML_TEST_0/64b HTTP/1.0
    GET /YAML_TEST_1/64b HTTP/1.0
    GET /YAML_TEST_2/64b HTTP/1.0
    ```
    
    Command a: `wb -U YAML_TEST_ -n 3 10.0.1.131:18081`
    
    Command b: `wb -F get64b.pkt -J [PACKET_SEQ_ID] -n 3 10.0.1.131:18081`
    Packet file "get64b.pkt" has the [PACKET_SEQ_ID] in its header like this:
    
    ```
    GET /YAML_TEST_[PACKET_SEQ_ID]/64b HTTP/1.0
    Host: localhost
    User-Agent: ApacheBench/2.3
    Accept: */*
    ```

## Build Instructions

### Build   

```
make clean
make
```    

### Install

```
make install
```

## Usage

### Normal ab-like testing with only 1 step

```
wb -t 10 live.com/home.html
```

Benchmark "live.com/home.html" for 10 seconds just like ab.

### WAF performance testing

```
wb -t 10 -c 20 10.0.1.131:18081
```

The three options are:    

* duration of testing (-t 10, 10 seconds) 
* connection number (-c 20) 
* destination server/URL (10.0.1.131:18081). Note that, unlike ab, wb does not require "/" at the end of URL.

### Examples

There are several examples in `../example/` to help understanding usage.

- `WB-GET.sh` uses `wb` to conduct GET test.
- `WB-POST.sh` uses `wb` to conduct POST test.
- `WB-SEND-PACKET.sh` uses `wb` to send HTTP packets directly.

## Synopsis

```
    wb [ -A auth-username:password ] [ -b windowsize ] [ -B local-address
    ] [ -c concurrency ] [ -C cookie-name=value ] [ -d ] [ -e csv-file ]
    [ -f protocol ] [ -F pkt_file ] [ -g gnuplot-file ] [ -G max_size ]
    [ -h ] [ -H custom-header ] [ -i ] [ -j interval ] [ -J sub_string ]
    [ -k ] [ -K ] [ -l ] [ -m HTTP-method ] [ -n requests ] [ -o msg_file
    ] [ -p POST-file ] [ -P proxy-auth-username:password ] [ -q ] [
    -Q max_count ] [ -r ] [ -s timeout ] [ -S ] [ -t timelimit ] [ -T
    content-type ] [ -u PUT-file ] [ -U URL_prefix ] [ -v verbosity] [ -V
    ] [ -w ] [ -W stats_num ] [ -x <table>-attributes ] [ -X proxy[:port]
    ] [ -y <tr>-attributes ] [ -z <td>-attributes ] [ -Z ciphersuite ]
    [ -1 ] [ -2 ] [ -3 ] [http[s]://]hostname[:port]/path
```

## Options

## Classical ApacheBench's Options

```
    -A auth-username:password
        Supply BASIC Authentication credentials to the server. The
        username and password are separated by a single : and sent on
        the wire base64 encoded. The string is sent regardless of whether
        the server needs it (i.e., has sent an 401 authentication needed).

    -b windowsize
        Size of TCP send/receive buffer, in bytes.

    -B local-address
        Address to bind to when making outgoing connections.

    -c concurrency
        Number of multiple requests to perform at a time. Default is
        one request at a time.

    -C cookie-name=value
        Add a Cookie: line to the request. The argument is typically in
        the form of a name=value pair. This field is repeatable.

    -d
        Do not display the "percentage served within XX [ms]
        table". (legacy support).

    -e csv-file
        Write a Comma separated value (CSV) file which contains for each
        percentage (from 1% to 100%) the time (in milliseconds) it took to
        serve that percentage of the requests. This is usually more useful
        than the 'gnuplot' file; as the results are already 'binned'.

    -f protocol
        Specify SSL/TLS protocol (SSL2, SSL3, TLS1, TLS1.1, TLS1.2,
        or ALL). TLS1.1 and TLS1.2 support available in 2.4.4 and later.

    -g gnuplot-file
        Write all measured values out as a 'gnuplot' or TSV (Tab separate
        values) file. This file can easily be imported into packages
        like Gnuplot, IDL, Mathematica, Igor or even Excel. The labels
        are on the first line of the file.

    -h
        Display usage information.

    -H custom-header
        Append extra headers to the request. The argument is typically
        in the form of a valid header line, containing a colon-separated
        field-value pair (i.e., "Accept-Encoding: zip/zop;8bit").

    -i
        Do HEAD requests instead of GET.

    -k
        Enable the HTTP KeepAlive feature, i.e., perform multiple requests
        within one HTTP session. Default is no KeepAlive.

    -l
        Do not report errors if the length of the responses is not
        constant. This can be useful for dynamic pages. Available in
        2.4.7 and later.

    -m HTTP-method
        Custom HTTP method for the requests. Available in 2.4.10 and
        later.

    -n requests
        Number of requests to perform for the benchmarking session. The
        default is to just perform a single request which usually leads
        to non-representative benchmarking results.

    -p POST-file
        File containing data to POST. Remember to also set -T.

    -P proxy-auth-username:password
        Supply BASIC Authentication credentials to a proxy en-route. The
        username and password are separated by a single : and sent on the
        wire base64 encoded. The string is sent regardless of whether
        the proxy needs it (i.e., has sent an 407 proxy authentication
        needed).

    -q
        When processing more than 150 requests, ab outputs a progress
        count on stderr every 10% or 100 requests or so. The -q flag
        will suppress these messages.

    -r
        Don't exit on socket receive errors.

    -s timeout
        Maximum number of seconds to wait before the socket times
        out. Default is 30 seconds. Available in 2.4.4 and later.

    -S
        Do not display the median and standard deviation values, nor
        display the warning/error messages when the average and median
        are more than one or two times the standard deviation apart. And
        default to the min/avg/max values. (legacy support).

    -t timelimit
        Maximum number of seconds to spend for benchmarking. This
        implies a -n 50000 internally. Use this to benchmark the server
        within a fixed total amount of time. Per default there is no
        timelimit. (implicit "-n 50000" is removed in wb)

    -T content-type
        Content-type header to use for POST/PUT data,
        eg. application/x-www-form-urlencoded. Default is text/plain.

    -u PUT-file
        File containing data to PUT. Remember to also set -T.

    -v verbosity
        Set verbosity level - 4 and above prints information on headers,
        3 and above prints response codes (404, 200, etc.), 2 and above
        prints warnings and info.

    -V
        Display version number and exit.

    -w
        Print out results in HTML tables. Default table is two columns
        wide, with a white background.

    -x <table>-attributes
        String to use as attributes for <table>. Attributes are inserted
        <table here >.

    -X proxy[:port]
        Use a proxy server for the requests.

    -y <tr>-attributes
        String to use as attributes for <tr>.

    -z <td>-attributes
        String to use as attributes for <td>.

    -Z ciphersuite
        Specify SSL/TLS cipher suite (See openssl ciphers)
```

## WAF-Bench's New Options

```
    -F pkt_file     File of packet seperated by \0 or a leading size
                    note: "-n" now is the total times to be sent for pkt_file
    -G max_size     Maximum output file size (in MB, default=0:unlimited)
    -j interval     Progress report interval (set 0 to disable, default=1)
    -J sub_string   Replace the sub_string in pkt content with <seq#> of wb
    -K              Keep body during save (default: save header only)
    -o msg_file     Save received http messages to filename
    -Q max_count    # of packets in packet file (default=0:all pkts in file)
    -U URL_prefix   Add prefix "/URL_prefix<seq#>/" to each request URL
    -W stats_num    Window of stats, number of stats values (default=50000)
    -1              (for testing) Don't append Host:localhost if absent (
                    default to add)
    -2 option       (for testing)  Don't append Connection:close if option is 0,
                    Append connection:close to those packets without connection attribution if option is 1,
                    Append or replace connection attribution to close for any packets if option is 2
    -3              (for testing) Use micro-second granularity in output,
                    default disabled
```

## Packet Format

**Note**: Because handwritten packets are error-prone, we highly recommend you to edit the information of packets with YAML format and it can be directly sent by [`pywb`](../pywb).

This section describes the format of the packet file used in wb's `-F` option.

Packet file consists of serveral HTTP requests. There are two ways to separate requests:

1. Put a size before each request, which is the size in bytes of the following request.
2. Delimit requests by a NUL character, i.e. `\0`.

For example, we have two requests: A and B.

A's content is:

```
GET / HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
If-None-Match: "1541025663+gzip"
If-Modified-Since: Fri, 09 Aug 2013 23:54:35 GMT
```

A's size in bytes is 476.

B's content is:

```
GET /test HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
```

B's size in bytes is 398.

If you use the size way, the packect file will be:

```
476
GET / HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
If-None-Match: "1541025663+gzip"
If-Modified-Since: Fri, 09 Aug 2013 23:54:35 GMT
398
GET /test HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
```

If you use the `\0` way, the packect file will be:

```
GET / HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
If-None-Match: "1541025663+gzip"
If-Modified-Since: Fri, 09 Aug 2013 23:54:35 GMT
\0
GET /test HTTP/1.1
Host: example.com
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
```

Actually, `\0` is not visible, but for demonstration, it is showed explicitly.

## Notes

There are various statically declared buffers of fixed length. Combined with the lazy parsing of the command line arguments, the response headers from the server and other external inputs, this might bite you.

It does not implement HTTP/1.x fully; only accepts some 'expected' forms of  responses. The rather heavy use of strstr(3) shows up top in profile, which might indicate a performance problem; i.e., you would measure the ab performance rather than the server's.
