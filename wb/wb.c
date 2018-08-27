/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
   ** This program is based on ZeusBench V1.0 written by Adam Twiss
   ** which is Copyright (c) 1996 by Zeus Technology Ltd. http://www.zeustech.net/
   **
   ** This software is provided "as is" and any express or implied waranties,
   ** including but not limited to, the implied warranties of merchantability and
   ** fitness for a particular purpose are disclaimed.  In no event shall
   ** Zeus Technology Ltd. be liable for any direct, indirect, incidental, special,
   ** exemplary, or consequential damaged (including, but not limited to,
   ** procurement of substitute good or services; loss of use, data, or profits;
   ** or business interruption) however caused and on theory of liability.  Whether
   ** in contract, strict liability or tort (including negligence or otherwise)
   ** arising in any way out of the use of this software, even if advised of the
   ** possibility of such damage.
   **
 */

/*
   ** HISTORY:
   **    - Originally written by Adam Twiss <adam@zeus.co.uk>, March 1996
   **      with input from Mike Belshe <mbelshe@netscape.com> and
   **      Michael Campanella <campanella@stevms.enet.dec.com>
   **    - Enhanced by Dean Gaudet <dgaudet@apache.org>, November 1997
   **    - Cleaned up by Ralf S. Engelschall <rse@apache.org>, March 1998
   **    - POST and verbosity by Kurt Sussman <kls@merlot.com>, August 1998
   **    - HTML table output added by David N. Welton <davidw@prosa.it>, January 1999
   **    - Added Cookie, Arbitrary header and auth support. <dirkx@webweaving.org>, April 1999
   ** Version 1.3d
   **    - Increased version number - as some of the socket/error handling has
   **      fundamentally changed - and will give fundamentally different results
   **      in situations where a server is dropping requests. Therefore you can
   **      no longer compare results of AB as easily. Hence the inc of the version.
   **      They should be closer to the truth though. Sander & <dirkx@covalent.net>, End 2000.
   **    - Fixed proxy functionality, added median/mean statistics, added gnuplot
   **      output option, added _experimental/rudimentary_ SSL support. Added
   **      confidence guestimators and warnings. Sander & <dirkx@covalent.net>, End 2000
   **    - Fixed serious int overflow issues which would cause realistic (longer
   **      than a few minutes) run's to have wrong (but believable) results. Added
   **      trapping of connection errors which influenced measurements.
   **      Contributed by Sander Temme, Early 2001
   ** Version 1.3e
   **    - Changed timeout behavour during write to work whilst the sockets
   **      are filling up and apr_write() does writes a few - but not all.
   **      This will potentially change results. <dirkx@webweaving.org>, April 2001
   ** Version 2.0.36-dev
   **    Improvements to concurrent processing:
   **      - Enabled non-blocking connect()s.
   **      - Prevent blocking calls to apr_socket_recv() (thereby allowing AB to
   **        manage its entire set of socket descriptors).
   **      - Any error returned from apr_socket_recv() that is not EAGAIN or EOF
   **        is now treated as fatal.
   **      Contributed by Aaron Bannert, April 24, 2002
   **
   ** Version 2.0.36-2
   **     Internalized the version string - this string is part
   **     of the Agent: header and the result output.
   **
   ** Version 2.0.37-dev
   **     Adopted SSL code by Madhu Mathihalli <madhusudan_mathihalli@hp.com>
   **     [PATCH] ab with SSL support  Posted Wed, 15 Aug 2001 20:55:06 GMT
   **     Introduces four 'if (int == value)' tests per non-ssl request.
   **
   ** Version 2.0.40-dev
   **     Switched to the new abstract pollset API, allowing ab to
   **     take advantage of future apr_pollset_t scalability improvements.
   **     Contributed by Brian Pane, August 31, 2002
   **
   ** Version 2.3
   **     SIGINT now triggers output_results().
   **     Contributed by colm, March 30, 2006
   **/

/* Note: this version string should start with \d+[\d\.]* and be a valid
 * string for an HTTP Agent: header when prefixed with 'ApacheBench/'.
 * It should reflect the version of AB - and not that of the apache server
 * it happens to accompany. And it should be updated or changed whenever
 * the results are no longer fundamentally comparable to the results of
 * a previous version of ab. Either due to a change in the logic of
 * ab - or to due to a change in the distribution it is compiled with
 * (such as an APR change in for example blocking).
 */

/*
 * standalone ApacheBench(ab): from https://github.com/CloudFundoo/ApacheBench-ab
 * latest ab.c: from https://svn.apache.org/repos/asf/httpd/httpd/trunk/support/
 *        First commit: oversion=GC5c2033675aaa3f14ecbae9dfa42695db2cf5fbd3
 * ab.c on github mirror site: https://github.com/apache/httpd/tree/trunk/support
 *        latest Revision 1828388 (2018-04-05)
 * TODOs: 
 *       1) Multi-thread support (-N)
 *       2) Request length > 8192 (ab's limitation)
 */
 // user can decide to compile wb in Makefile (-D_WAF_BENCH_), or forced compiling
 // #define _WAF_BENCH_  // this is for forced WAF_Bench compiling

#define AP_AB_BASEREVISION "2.3"

/*
 * BUGS:
 *
 * - uses strcpy/etc.
 * - has various other poor buffer attacks related to the lazy parsing of
 *   response headers from the server
 * - doesn't implement much of HTTP/1.x, only accepts certain forms of
 *   responses
 * - (performance problem) heavy use of strstr shows up top in profile
 *   only an issue for loopback usage
 */

/*  -------------------------------------------------------------------- */

#if 'A' != 0x41
/* Hmmm... This source code isn't being compiled in ASCII.
 * In order for data that flows over the network to make
 * sense, we need to translate to/from ASCII.
 */
#define NOT_ASCII
#endif

/* affects include files on Solaris */
#define BSD_COMP

#include "apr.h"
#include "apr_signal.h"
#include "apr_strings.h"
#include "apr_network_io.h"
#include "apr_file_io.h"
#include "apr_time.h"
#include "apr_getopt.h"
#include "apr_general.h"
#include "apr_lib.h"
#include "apr_portable.h"
#include "ap_release.h"
#include "apr_poll.h"

#define APR_WANT_STRFUNC
#include "apr_want.h"

#include "apr_base64.h"
#ifdef NOT_ASCII
#include "apr_xlate.h"
#endif
#if APR_HAVE_STDIO_H
#include <stdio.h>
#endif
#if APR_HAVE_STDLIB_H
#include <stdlib.h>
#endif
#if APR_HAVE_UNISTD_H
#include <unistd.h> /* for getpid() */
#endif

#if !defined(WIN32) && !defined(NETWARE)
//#include "ap_config_auto.h" // we have to comment out this header so as to compile in our environment, don't know why?
#endif

#if defined(HAVE_OPENSSL)

#include <openssl/rsa.h>
#include <openssl/crypto.h>
#include <openssl/x509.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <openssl/rand.h>
#define USE_SSL
#define SK_NUM(x) sk_X509_num(x)
#define SK_VALUE(x,y) sk_X509_value(x,y)
typedef STACK_OF(X509) X509_STACK_TYPE;

#if defined(_MSC_VER)
/* The following logic ensures we correctly glue FILE* within one CRT used
 * by the OpenSSL library build to another CRT used by the ab.exe build.
 * This became especially problematic with Visual Studio 2015.
 */
#include <openssl/applink.c>
#endif

#endif

#if defined(USE_SSL)
#if (OPENSSL_VERSION_NUMBER >= 0x00909000)
#define AB_SSL_METHOD_CONST const
#else
#define AB_SSL_METHOD_CONST
#endif
#if (OPENSSL_VERSION_NUMBER >= 0x0090707f)
#define AB_SSL_CIPHER_CONST const
#else
#define AB_SSL_CIPHER_CONST
#endif
#ifdef SSL_OP_NO_TLSv1_2
#define HAVE_TLSV1_X
#endif
#if !defined(OPENSSL_NO_TLSEXT) && defined(SSL_set_tlsext_host_name)
#define HAVE_TLSEXT
#endif
#if defined(LIBRESSL_VERSION_NUMBER) && LIBRESSL_VERSION_NUMBER < 0x2060000f
#define SSL_CTRL_SET_MIN_PROTO_VERSION 123
#define SSL_CTRL_SET_MAX_PROTO_VERSION 124
#define SSL_CTX_set_min_proto_version(ctx, version) \
   SSL_CTX_ctrl(ctx, SSL_CTRL_SET_MIN_PROTO_VERSION, version, NULL)
#define SSL_CTX_set_max_proto_version(ctx, version) \
   SSL_CTX_ctrl(ctx, SSL_CTRL_SET_MAX_PROTO_VERSION, version, NULL)
#endif
#endif

#include <math.h>
#if APR_HAVE_CTYPE_H
#include <ctype.h>
#endif
#if APR_HAVE_LIMITS_H
#include <limits.h>
#endif

/* ------------------- DEFINITIONS -------------------------- */

#ifndef LLONG_MAX
#define AB_MAX APR_INT64_C(0x7fffffffffffffff)
#else
#define AB_MAX LLONG_MAX
#endif

/* maximum number of requests on a time limited test */
#define MAX_REQUESTS (INT_MAX > 50000 ? 50000 : INT_MAX)

/* connection state
 * don't add enums or rearrange or otherwise change values without
 * visiting set_conn_state()
 */
typedef enum {
    STATE_UNCONNECTED = 0,
    STATE_CONNECTING,           /* TCP connect initiated, but we don't
                                 * know if it worked yet
                                 */
    STATE_CONNECTED,            /* we know TCP connect completed */
    STATE_READ
} connect_state_e;

#define CBUFFSIZE (8192)

struct connection {
    apr_pool_t *ctx;
    apr_socket_t *aprsock;
    apr_pollfd_t pollfd;
    int state;
    apr_size_t read;            /* amount of bytes read */
    apr_size_t bread;           /* amount of body read */
    apr_size_t rwrite, rwrote;  /* keep pointers in what we write - across
                                 * EAGAINs */
    apr_size_t length;          /* Content-Length value used for keep-alive */
    char cbuff[CBUFFSIZE];      /* a buffer to store server response header */
    int cbx;                    /* offset in cbuffer */
    int keepalive;              /* non-zero if a keep-alive request */
    int gotheader;              /* non-zero if we have the entire header in
                                 * cbuff */
    apr_time_t start,           /* Start of connection */
               connect,         /* Connected, start writing */
               endwrite,        /* Request written */
               beginread,       /* First byte of input */
               done;            /* Connection closed */

    int socknum;
#ifdef USE_SSL
    SSL *ssl;
#endif
};

struct data {
    apr_time_t starttime;         /* start time of connection */
    apr_interval_time_t waittime; /* between request and reading response */
    apr_interval_time_t ctime;    /* time to connect */
    apr_interval_time_t time;     /* time for connection */
};

#define ap_min(a,b) (((a)<(b))?(a):(b))
#define ap_max(a,b) (((a)>(b))?(a):(b))
#define ap_round_ms(a) ((apr_time_t)((a) + 500)/1000)
#define ap_double_ms(a) ((double)(a)/1000.0)
#define MAX_CONCURRENCY 20000

/* --------------------- GLOBALS ---------------------------- */

#ifdef _WAF_BENCH_  // globals and definitions for WAF_BENCH

#define WAF_BENCH_VERSION   "1.2.1" /* start from version 0.1.0, now it's 1.2.1           */
#define WAF_BENCH_SUBVERSION "2018-08-14-11:46:05" /* subversion, using git commit time */
#define INI_FILENAME        "wb.ini"/* ini file filename                                */
#define DEFAULT_TEST_TIME   5       /* default test time in seconds                     */
#define MB                  1000000/* Million Bytes                                    */

// Global variables
int g_us_granularity = 1;           /* microsec-granularity in output-results           */
int g_extended_progress = 0;        /* printout additional progress report              */
int g_stats_window = MAX_REQUESTS;  /* how many stats results, "-W" option              */
int g_enable_ini = 0;               /* "-0", enable read/write ini for wb's options     */
int g_add_localhost = 1;            /* "-1", add header host:localhost if not present   */
int g_add_connection_close = 1;     /* '-2', add header connection:close if not present */
int g_save_body = 0;                /* '-K', keep body when save                        */
apr_file_t *g_save_file_fd = NULL;  /* save received messages to output file            */
ulong g_MAX_FILE_SIZE = 0;          /* default output file size, unlimited              */
ulong g_saved_bytes = 0;            /* how many bytes saved to file                     */
apr_size_t g_pkt_length = 0;        /* length of file for packets to be sent            */
char *g_pkt_data;                   /* global buffer containing data from pktfile       */
struct _g_pkt_array_                /* save the starting pointer of those sent packets  */
{
    char    *pkt_data;
    int     pkt_length;
	apr_time_t pkt_time_to_send;
} *g_pkt_array;
ulong g_pkt_count = 0;              /* number of packets which have been sent           */
ulong g_MAX_PKT_COUNT = 0;          /* max # of packets , default: 0 means all packets  */
ulong g_RPS_NUMBER = 0;             /* RPS for rate limiting, default: 0 means no limit */

int g_interval_print = 1;           /* Interval (in secs) of printing progress report   */
int g_set_requests = 0;             /* whether requests is specified with "-n" option   */

const char *g_save_filename;        /* save received messages to filename               */
const char *g_pkt_filename;         /* read packets from filename                       */
const char *g_put_filename;         /* read put body from filename                      */
const char *g_post_filename;        /* read post body from filename                     */
const char *opt_file_in;            /* input options file                               */
const char *opt_file_out;           /* output options file                              */
const char *g_opt_prefix;           /* Add prefix("/prefix<seq#>/" to each request      */
char *g_header_to_sent;             /* to store the generated header to be sent         */
char *g_new_header;                 /* to store the generated prefix                    */
char *g_request_end = NULL;         /* store the end position of request header         */
apr_size_t g_new_header_len = 0;    /* length of generated new header                   */
apr_size_t g_header_len_MAX = 8192; /* max length of generated new header               */
char **g_sub_string;                /* to store the sub_string that's to be replaced    */
apr_size_t g_sub_string_num = 0;    /* number of sub strings                            */
apr_size_t g_sub_string_num_MAX=128;/* maximum number of sub strings                    */

// Global options
int opt_connection = 0;             /* was an optional "Connection:" header specified?  */
char *opt_string;                   /* options input/output from/to the file            */
char **g_argv_ini;                  /* argv from ini file                               */
int g_argc_ini;                     /* argc from ini file                               */
int g_opt_string_len = 8192;        /* option string length from ini file               */
int g_keepalive_for_real_traffic=0; /* keep alive option for real traffic testing       */
#endif //_WAF_BENCH_  // globals and definitions for WAF_BENCH

int verbosity = 0;      /* no verbosity by default */
int recverrok = 0;      /* ok to proceed after socket receive errors */
enum {NO_METH = 0, GET, HEAD, PUT, POST, CUSTOM_METHOD} method = NO_METH;
const char *method_str[] = {"bug", "GET", "HEAD", "PUT", "POST", ""};
int send_body = 0;      /* non-zero if sending body with request */
int requests = 1;       /* Number of requests to make */
int heartbeatres = 100; /* How often do we say we're alive */
int concurrency = 1;    /* Number of multiple requests to make */
int percentile = 1;     /* Show percentile served */
int nolength = 0;       /* Accept variable document length */
int confidence = 1;     /* Show confidence estimator and warnings */
int tlimit = 0;         /* time limit in secs */
int keepalive = 0;      /* try and do keepalive connections */
int windowsize = 0;     /* we use the OS default window size */
char servername[1024];  /* name that server reports */
char *hostname;         /* host name from URL */
const char *host_field;       /* value of "Host:" header field */
const char *path;             /* path name */
char *postdata;         /* *buffer containing data from postfile */
apr_size_t postlen = 0; /* length of data to be POSTed */
char *content_type = NULL;     /* content type to put in POST header */
const char *cookie,           /* optional cookie line */
           *auth,             /* optional (basic/uuencoded) auhentication */
           *hdrs;             /* optional arbitrary headers */
apr_port_t port;        /* port number */
char *proxyhost = NULL; /* proxy host name */
int proxyport = 0;      /* proxy port */
const char *connecthost;
const char *myhost;
apr_port_t connectport;
const char *gnuplot;          /* GNUplot file */
const char *csvperc;          /* CSV Percentile file */
const char *fullurl;
const char *colonhost;
int isproxy = 0;
apr_interval_time_t aprtimeout = apr_time_from_sec(30); /* timeout value */

/* overrides for ab-generated common headers */
const char *opt_host;   /* which optional "Host:" header specified, if any */
int opt_useragent = 0;  /* was an optional "User-Agent:" header specified? */
int opt_accept = 0;     /* was an optional "Accept:" header specified? */
 /*
  * XXX - this is now a per read/write transact type of value
  */

int use_html = 0;       /* use html in the report */
const char *tablestring;
const char *trstring;
const char *tdstring;

apr_size_t doclen = 0;     /* the length the document should be */
apr_int64_t totalread = 0;    /* total number of bytes read */
apr_int64_t totalbread = 0;   /* totoal amount of entity body read */
apr_int64_t totalposted = 0;  /* total number of bytes posted, inc. headers */
int started = 0;           /* number of requests started, so no excess */
int done = 0;              /* number of requests we have done */
int doneka = 0;            /* number of keep alive connections done */
int good = 0, bad = 0;     /* number of good and bad requests */
int epipe = 0;             /* number of broken pipe writes */
int err_length = 0;        /* requests failed due to response length */
int err_conn = 0;          /* requests failed due to connection drop */
int err_recv = 0;          /* requests failed due to broken read */
int err_except = 0;        /* requests failed due to exception */
int err_response = 0;      /* requests with invalid or non-200 response */

#ifdef USE_SSL
int is_ssl;
SSL_CTX *ssl_ctx;
char *ssl_cipher = NULL;
char *ssl_info = NULL;
char *ssl_tmp_key = NULL;
BIO *bio_out,*bio_err;
#ifdef HAVE_TLSEXT
int tls_use_sni = 1;         /* used by default, -I disables it */
const char *tls_sni = NULL; /* 'opt_host' if any, 'hostname' otherwise */
#endif
#endif

apr_time_t start, lasttime, stoptime;

/* global request (and its length) */
char _request[8192];
char *request = _request;
apr_size_t reqlen;
int requests_initialized = 0;

/* one global throw-away buffer to read stuff into */
char buffer[8192];

/* interesting percentiles */
int percs[] = {50, 66, 75, 80, 90, 95, 98, 99, 100};

struct connection *con;     /* connection array */
struct data *stats;         /* data for each request */
apr_pool_t *cntxt;

apr_pollset_t *readbits;

apr_sockaddr_t *mysa;
apr_sockaddr_t *destsa;

#ifdef NOT_ASCII
apr_xlate_t *from_ascii, *to_ascii;
#endif

static void write_request(struct connection * c);
static void close_connection(struct connection * c);

/* --------------------------------------------------------- */

/* simple little function to write an error string and exit */

static void err(const char *s)
{
    fprintf(stderr, "%s\n", s);
    if (done)
        printf("Total of %d requests completed\n" , done);
    exit(1);
}

/* simple little function to write an APR error string and exit */

static void apr_err(const char *s, apr_status_t rv)
{
    char buf[120];

    fprintf(stderr,
        "%s: %s (%d)\n",
        s, apr_strerror(rv, buf, sizeof buf), rv);
    if (done)
        printf("Total of %d requests completed\n" , done);
    exit(rv);
}

static void *xmalloc(size_t size)
{
    void *ret = malloc(size);
    if (ret == NULL) {
        fprintf(stderr, "Could not allocate memory (%"
                APR_SIZE_T_FMT" bytes)\n", size);
        exit(1);
    }
    return ret;
}

static void *xcalloc(size_t num, size_t size)
{
    void *ret = calloc(num, size);
    if (ret == NULL) {
        fprintf(stderr, "Could not allocate memory (%"
                APR_SIZE_T_FMT" bytes)\n", size*num);
        exit(1);
    }
    return ret;
}

static char *xstrdup(const char *s)
{
    char *ret = strdup(s);
    if (ret == NULL) {
        fprintf(stderr, "Could not allocate memory (%"
                APR_SIZE_T_FMT " bytes)\n", strlen(s));
        exit(1);
    }
    return ret;
}

/*
 * Similar to standard strstr() but we ignore case in this version.
 * Copied from ap_strcasestr().
 */
static char *xstrcasestr(const char *s1, const char *s2)
{
    char *p1, *p2;
    if (*s2 == '\0') {
        /* an empty s2 */
        return((char *)s1);
    }
    while(1) {
        for ( ; (*s1 != '\0') && (apr_tolower(*s1) != apr_tolower(*s2)); s1++);
        if (*s1 == '\0') {
            return(NULL);
        }
        /* found first character of s2, see if the rest matches */
        p1 = (char *)s1;
        p2 = (char *)s2;
        for (++p1, ++p2; apr_tolower(*p1) == apr_tolower(*p2); ++p1, ++p2) {
            if (*p1 == '\0') {
                /* both strings ended together */
                return((char *)s1);
            }
        }
        if (*p2 == '\0') {
            /* second string ended, a match */
            break;
        }
        /* didn't find a match here, try starting at next character in s1 */
        s1++;
    }
    return((char *)s1);
}

/* pool abort function */
static int abort_on_oom(int retcode)
{
    fprintf(stderr, "Could not allocate memory\n");
    exit(1);
    /* not reached */
    return retcode;
}

static void set_polled_events(struct connection *c, apr_int16_t new_reqevents)
{
    apr_status_t rv;

    if (c->pollfd.reqevents != new_reqevents) {
        if (c->pollfd.reqevents != 0) {
            rv = apr_pollset_remove(readbits, &c->pollfd);
            if (rv != APR_SUCCESS) {
                apr_err("apr_pollset_remove()", rv);
            }
        }

        if (new_reqevents != 0) {
            c->pollfd.reqevents = new_reqevents;
            rv = apr_pollset_add(readbits, &c->pollfd);
            if (rv != APR_SUCCESS) {
                apr_err("apr_pollset_add()", rv);
            }
        }
    }
}

static void set_conn_state(struct connection *c, connect_state_e new_state)
{
    apr_int16_t events_by_state[] = {
        0,           /* for STATE_UNCONNECTED */
        APR_POLLOUT, /* for STATE_CONNECTING */
        APR_POLLIN,  /* for STATE_CONNECTED; we don't poll in this state,
                      * so prepare for polling in the following state --
                      * STATE_READ
                      */
        APR_POLLIN   /* for STATE_READ */
    };

    c->state = new_state;

    set_polled_events(c, events_by_state[new_state]);
}

/* --------------------------------------------------------- */
/* write out request to a connection - assumes we can write
 * (small) request out in one go into our new socket buffer
 *
 */
#ifdef USE_SSL
static long ssl_print_cb(BIO *bio,int cmd,const char *argp,int argi,long argl,long ret)
{
    BIO *out;

    out=(BIO *)BIO_get_callback_arg(bio);
    if (out == NULL) return(ret);

    if (cmd == (BIO_CB_READ|BIO_CB_RETURN)) {
        BIO_printf(out,"read from %p [%p] (%d bytes => %ld (0x%lX))\n",
                   bio, argp, argi, ret, ret);
        BIO_dump(out,(char *)argp,(int)ret);
        return(ret);
    }
    else if (cmd == (BIO_CB_WRITE|BIO_CB_RETURN)) {
        BIO_printf(out,"write to %p [%p] (%d bytes => %ld (0x%lX))\n",
                   bio, argp, argi, ret, ret);
        BIO_dump(out,(char *)argp,(int)ret);
    }
    return ret;
}

static void ssl_state_cb(const SSL *s, int w, int r)
{
    if (w & SSL_CB_ALERT) {
        BIO_printf(bio_err, "SSL/TLS Alert [%s] %s:%s\n",
                   (w & SSL_CB_READ ? "read" : "write"),
                   SSL_alert_type_string_long(r),
                   SSL_alert_desc_string_long(r));
    } else if (w & SSL_CB_LOOP) {
        BIO_printf(bio_err, "SSL/TLS State [%s] %s\n",
                   (SSL_in_connect_init((SSL*)s) ? "connect" : "-"),
                   SSL_state_string_long(s));
    } else if (w & (SSL_CB_HANDSHAKE_START|SSL_CB_HANDSHAKE_DONE)) {
        BIO_printf(bio_err, "SSL/TLS Handshake [%s] %s\n",
                   (w & SSL_CB_HANDSHAKE_START ? "Start" : "Done"),
                   SSL_state_string_long(s));
    }
}

#ifndef RAND_MAX
#define RAND_MAX INT_MAX
#endif

static int ssl_rand_choosenum(int l, int h)
{
    int i;
    char buf[50];

    srand((unsigned int)time(NULL));
    apr_snprintf(buf, sizeof(buf), "%.0f",
                 (((double)(rand()%RAND_MAX)/RAND_MAX)*(h-l)));
    i = atoi(buf)+1;
    if (i < l) i = l;
    if (i > h) i = h;
    return i;
}

static void ssl_rand_seed(void)
{
    int n, l;
    time_t t;
    pid_t pid;
    unsigned char stackdata[256];

    /*
     * seed in the current time (usually just 4 bytes)
     */
    t = time(NULL);
    l = sizeof(time_t);
    RAND_seed((unsigned char *)&t, l);

    /*
     * seed in the current process id (usually just 4 bytes)
     */
    pid = getpid();
    l = sizeof(pid_t);
    RAND_seed((unsigned char *)&pid, l);

    /*
     * seed in some current state of the run-time stack (128 bytes)
     */
    n = ssl_rand_choosenum(0, sizeof(stackdata)-128-1);
    RAND_seed(stackdata+n, 128);
}

static int ssl_print_connection_info(BIO *bio, SSL *ssl)
{
    AB_SSL_CIPHER_CONST SSL_CIPHER *c;
    int alg_bits,bits;

    BIO_printf(bio,"Transport Protocol      :%s\n", SSL_get_version(ssl));

    c = SSL_get_current_cipher(ssl);
    BIO_printf(bio,"Cipher Suite Protocol   :%s\n", SSL_CIPHER_get_version(c));
    BIO_printf(bio,"Cipher Suite Name       :%s\n",SSL_CIPHER_get_name(c));

    bits = SSL_CIPHER_get_bits(c,&alg_bits);
    BIO_printf(bio,"Cipher Suite Cipher Bits:%d (%d)\n",bits,alg_bits);

    return(1);
}

static void ssl_print_cert_info(BIO *bio, X509 *cert)
{
    X509_NAME *dn;
    EVP_PKEY *pk;
    char buf[1024];

    BIO_printf(bio, "Certificate version: %ld\n", X509_get_version(cert)+1);
    BIO_printf(bio,"Valid from: ");
    ASN1_UTCTIME_print(bio, X509_get_notBefore(cert));
    BIO_printf(bio,"\n");

    BIO_printf(bio,"Valid to  : ");
    ASN1_UTCTIME_print(bio, X509_get_notAfter(cert));
    BIO_printf(bio,"\n");

    pk = X509_get_pubkey(cert);
    BIO_printf(bio,"Public key is %d bits\n",
               EVP_PKEY_bits(pk));
    EVP_PKEY_free(pk);

    dn = X509_get_issuer_name(cert);
    X509_NAME_oneline(dn, buf, sizeof(buf));
    BIO_printf(bio,"The issuer name is %s\n", buf);

    dn=X509_get_subject_name(cert);
    X509_NAME_oneline(dn, buf, sizeof(buf));
    BIO_printf(bio,"The subject name is %s\n", buf);

    /* dump the extension list too */
    BIO_printf(bio, "Extension Count: %d\n", X509_get_ext_count(cert));
}

static void ssl_print_info(struct connection *c)
{
    X509_STACK_TYPE *sk;
    X509 *cert;
    int count;

    BIO_printf(bio_err, "\n");
    sk = SSL_get_peer_cert_chain(c->ssl);
    if ((count = SK_NUM(sk)) > 0) {
        int i;
        for (i=1; i<count; i++) {
            cert = (X509 *)SK_VALUE(sk, i);
            ssl_print_cert_info(bio_out, cert);
    }
    }
    cert = SSL_get_peer_certificate(c->ssl);
    if (cert == NULL) {
        BIO_printf(bio_out, "Anon DH\n");
    } else {
        BIO_printf(bio_out, "Peer certificate\n");
        ssl_print_cert_info(bio_out, cert);
        X509_free(cert);
    }
    ssl_print_connection_info(bio_err,c->ssl);
    SSL_SESSION_print(bio_err, SSL_get_session(c->ssl));
    }

static void ssl_proceed_handshake(struct connection *c)
{
    int do_next = 1;

    while (do_next) {
        int ret, ecode;

        ret = SSL_do_handshake(c->ssl);
        ecode = SSL_get_error(c->ssl, ret);

        switch (ecode) {
        case SSL_ERROR_NONE:
            if (verbosity >= 2)
                ssl_print_info(c);
            if (ssl_info == NULL) {
                AB_SSL_CIPHER_CONST SSL_CIPHER *ci;
                X509 *cert;
                int sk_bits, pk_bits, swork;

                ci = SSL_get_current_cipher(c->ssl);
                sk_bits = SSL_CIPHER_get_bits(ci, &swork);
                cert = SSL_get_peer_certificate(c->ssl);
                if (cert)
                    pk_bits = EVP_PKEY_bits(X509_get_pubkey(cert));
                else
                    pk_bits = 0;  /* Anon DH */

                ssl_info = xmalloc(128);
                apr_snprintf(ssl_info, 128, "%s,%s,%d,%d",
                             SSL_get_version(c->ssl),
                             SSL_CIPHER_get_name(ci),
                             pk_bits, sk_bits);
            }
            if (ssl_tmp_key == NULL) {
                EVP_PKEY *key;
                if (SSL_get_server_tmp_key(c->ssl, &key)) {
                    ssl_tmp_key = xmalloc(128);
                    switch (EVP_PKEY_id(key)) {
                    case EVP_PKEY_RSA:
                        apr_snprintf(ssl_tmp_key, 128, "RSA %d bits",
                                     EVP_PKEY_bits(key));
                        break;
                    case EVP_PKEY_DH:
                        apr_snprintf(ssl_tmp_key, 128, "DH %d bits",
                                     EVP_PKEY_bits(key));
                        break;
#ifndef OPENSSL_NO_EC
                    case EVP_PKEY_EC: {
                        const char *cname = NULL;
                        EC_KEY *ec = EVP_PKEY_get1_EC_KEY(key);
                        int nid = EC_GROUP_get_curve_name(EC_KEY_get0_group(ec));
                        EC_KEY_free(ec);
#if OPENSSL_VERSION_NUMBER >= 0x10002000L
                        cname = EC_curve_nid2nist(nid);
#endif
                        if (!cname)
                            cname = OBJ_nid2sn(nid);

                        apr_snprintf(ssl_tmp_key, 128, "ECDH %s %d bits",
                                     cname,
                                     EVP_PKEY_bits(key));
                        break;
                        }
#endif
                    }
                    EVP_PKEY_free(key);
                }
            }
            write_request(c);
            do_next = 0;
            break;
        case SSL_ERROR_WANT_READ:
            set_polled_events(c, APR_POLLIN);
            do_next = 0;
            break;
        case SSL_ERROR_WANT_WRITE:
            set_polled_events(c, APR_POLLOUT);
            do_next = 0;
            break;
        case SSL_ERROR_WANT_CONNECT:
        case SSL_ERROR_SSL:
        case SSL_ERROR_SYSCALL:
            /* Unexpected result */
            BIO_printf(bio_err, "SSL handshake failed (%d).\n", ecode);
            ERR_print_errors(bio_err);
            close_connection(c);
            do_next = 0;
            break;
        }
    }
}

#endif /* USE_SSL */

/* ------------------------------------------------------- */
#ifdef _WAF_BENCH_ // functions definitions

//  assign pkt id for each connection
int get_write_pkt_id(int connection_socket_id)
{
    int return_id;
    static int cur_id = 0;

    return_id = cur_id;

    // the simplest way is round-robin (cur_id ++)
    // we can do the assignment based on connection_socket_id later
    cur_id ++;
    if (cur_id == g_pkt_count)
        cur_id = 0;

    return return_id;
} // end of get_write_pkt_id

// write a string (end with '\0') to file with apr_file_write
static  apr_status_t apr_fprintf(apr_file_t *fd, char *string)
{
    apr_status_t rv;
    char errmsg[120];
    apr_size_t total_length, remain_length, next_save_length;

    remain_length = strlen(string);
    next_save_length = remain_length;
    total_length = remain_length;

    do {
        rv = apr_file_write(fd, string + (total_length - next_save_length), &next_save_length);

        if (rv != APR_SUCCESS) {
            fprintf(stderr, "wb: Could not write(%s) to file: %s\n", string,
                    apr_strerror(rv, errmsg, sizeof errmsg));
            return rv;
        }   
        remain_length -= next_save_length;
        next_save_length = remain_length;
    }   while (next_save_length > 0);
    return APR_SUCCESS;
} // end of apr_fprintf


// print out the benchmarking progress every interval
void print_progress(int forced_print )
{
    if (!forced_print && !g_interval_print) 
        return;
    
    static apr_time_t prev_heartbeat_time = 0;
    static int heartbeats_num = 0, prev_done = 0;
    static apr_time_t time_now, delta_t;
	static int prev_bad, prev_err_conn, prev_err_recv, prev_err_length, prev_err_except;
	static int prev_epipe, prev_err_response;
	static apr_int64_t prev_totalbread, prev_totalposted, prev_totalread;
	static int sample_start = 0;
	

    time_now = apr_time_now();
    if (forced_print || (time_now - prev_heartbeat_time >= g_interval_print)) {
        if (!prev_heartbeat_time) 
	            fprintf(stderr, "\n"); // first time, print the seperator
	    else if (g_extended_progress && (heartbeats_num % 50 == 0)){
				fprintf(stderr,"________________________________________________________________________________\n");
				fprintf(stderr, "Time Req(#/sec) Recv(kBps) ");
				if (send_body)
					fprintf(stderr, "Sent(kBps) ");
				fprintf(stderr, "Latency(min/max/mean[+/-sd] Failed(C/R/L/E/W/Non-2xx)");
				fprintf(stderr,"\n");
        }
		delta_t = time_now - prev_heartbeat_time;
        if (forced_print || prev_heartbeat_time) {
			if (!g_extended_progress) // print out simple info
            fprintf(stderr, "%2d: Completed %6d requests, rate is %lld #/sec.\n", 
                ++heartbeats_num, done, (long long int)(APR_USEC_PER_SEC * (done - prev_done)/delta_t));
			else { 	// print out additional info
		        apr_time_t totalcon = 0, total = 0, totald = 0, totalwait = 0;
		        apr_time_t meancon, meantot, meand, meanwait;
		        apr_interval_time_t mincon = AB_MAX, mintot = AB_MAX, mind = AB_MAX,
		                            minwait = AB_MAX;
		        apr_interval_time_t maxcon = 0, maxtot = 0, maxd = 0, maxwait = 0;
		        apr_interval_time_t mediancon = 0, mediantot = 0, mediand = 0, medianwait = 0;
		        double sdtot = 0, sdcon = 0, sdd = 0, sdwait = 0;
				int req_num = done - prev_done;	
				
				if (req_num > 0){
			        /* work out connection times */
			        int i;

			        for (i = 0; i < req_num; i++) {
			            struct data *s = &stats[(i+sample_start)%g_stats_window];
			            mincon = ap_min(mincon, s->ctime);
			            mintot = ap_min(mintot, s->time);
			            mind = ap_min(mind, s->time - s->ctime);
			            minwait = ap_min(minwait, s->waittime);

			            maxcon = ap_max(maxcon, s->ctime);
			            maxtot = ap_max(maxtot, s->time);
			            maxd = ap_max(maxd, s->time - s->ctime);
			            maxwait = ap_max(maxwait, s->waittime);

			            totalcon += s->ctime;
			            total += s->time;
			            totald += s->time - s->ctime;
			            totalwait += s->waittime;
			        }
			        meancon = totalcon / req_num;
			        meantot = total / req_num;
			        meand = totald / req_num;
			        meanwait = totalwait / req_num;

			        /* calculating the sample variance: the sum of the squared deviations, divided by n-1 */
			        for (i = 0; i < req_num; i++) {
			            struct data *s = &stats[(i+sample_start)%g_stats_window];
			            double a;
			            a = ((double)s->time - meantot);
			            sdtot += a * a;
			            a = ((double)s->ctime - meancon);
			            sdcon += a * a;
			            a = ((double)s->time - (double)s->ctime - meand);
			            sdd += a * a;
			            a = ((double)s->waittime - meanwait);
			            sdwait += a * a;
			        }

			        sdtot = (req_num > 1) ? sqrt(sdtot / (req_num - 1)) : 0;
			        sdcon = (req_num > 1) ? sqrt(sdcon / (req_num - 1)) : 0;
			        sdd = (req_num > 1) ? sqrt(sdd / (req_num - 1)) : 0;
			        sdwait = (req_num > 1) ? sqrt(sdwait / (req_num - 1)) : 0;

			        if (!g_us_granularity) {
						/*
						 * Reduce stats from apr time to milliseconds
						 */
						mincon     = ap_round_ms(mincon);
						mind       = ap_round_ms(mind);
						minwait    = ap_round_ms(minwait);
						mintot     = ap_round_ms(mintot);
						meancon    = ap_round_ms(meancon);
						meand      = ap_round_ms(meand);
						meanwait   = ap_round_ms(meanwait);
						meantot    = ap_round_ms(meantot);
						mediancon  = ap_round_ms(mediancon);
						mediand    = ap_round_ms(mediand);
						medianwait = ap_round_ms(medianwait);
						mediantot  = ap_round_ms(mediantot);
						maxcon     = ap_round_ms(maxcon);
						maxd       = ap_round_ms(maxd);
						maxwait    = ap_round_ms(maxwait);
						maxtot     = ap_round_ms(maxtot);
						sdcon      = ap_double_ms(sdcon);
						sdd        = ap_double_ms(sdd);
						sdwait     = ap_double_ms(sdwait);
						sdtot      = ap_double_ms(sdtot);
			       }
			    }			
				sample_start = (sample_start + req_num)%g_stats_window;
				
				//fprintf(stderr, "\nTime Req(#/sec) Recv(kBps) Failed(C/R/L/E/W/Non-2xx)");
				fprintf(stderr, "%-5d%-11lld%-11lld", 
						++heartbeats_num,  
						(long long int)(APR_USEC_PER_SEC * (done - prev_done)/delta_t),
						(long long int)(APR_USEC_PER_SEC * (totalread - prev_totalread)/delta_t/1000));
				if (send_body)
					//fprintf(stderr, "Sent(kBps) ");
					fprintf(stderr, "%-11lld", (long long int)(APR_USEC_PER_SEC*(totalposted - prev_totalposted)/delta_t/1000));

				//fprintf(stderr, "Latency(min/max/avg/+-sd) Failed(C/R/L/E/W/Non-2xx)");
				fprintf(stderr, "%-6lld/%-8lld/%-6lld/%-8.1f/",(long long int)mintot,(long long int)maxtot,(long long int)meantot,sdtot);
				fprintf(stderr, "%d", bad - prev_bad);
				if (bad) {
					fprintf(stderr, "(%d/%d/%d/%d/%d/%d)",
						err_conn - prev_err_conn,
						err_recv - prev_err_recv,
						err_length - prev_err_length,
						err_except - prev_err_except,
						epipe - prev_epipe,
						err_response - prev_err_response);
				}
				fprintf(stderr,"\n");
				prev_totalread = totalread;
				prev_totalposted = totalposted;
				prev_bad = bad;
				if (bad) {
					prev_err_conn=err_conn;
					prev_err_recv=err_recv;
					prev_err_length=err_length;
					prev_err_except=err_except;
					prev_epipe=epipe;
					prev_err_response=err_response;		
				}			

				
			}

            fflush(stderr);
            prev_done = done;
        }
        prev_heartbeat_time = time_now;

    }
} // end of print_progress

/* parse the packet strings */
static ulong parse_pktfile(char *pkt_data, struct _g_pkt_array_ *pkt_array);

/* compare to packet by time to send*/
int compare_pkt_by_time_to_send(const void * pkt1,const void * pkt2) {
    const struct _g_pkt_array_ * ppkt1 = (const struct _g_pkt_array_ *)pkt1;
    const struct _g_pkt_array_ * ppkt2 = (const struct _g_pkt_array_ *)pkt2;

    if (ppkt1->pkt_time_to_send < ppkt2->pkt_time_to_send) {
        return -1;
    } else if (ppkt1->pkt_time_to_send > ppkt2->pkt_time_to_send) {
        return 1;
    } else if (ppkt1->pkt_data < ppkt2->pkt_data) {
        return -1;
    } else if (ppkt1->pkt_data > ppkt2->pkt_data) {
        return 1;
    } else {
        return 0;
    }
}

/* read packets from file, save contents and length to global variables */
static apr_status_t open_pktfile(const char *pfile)
{
    apr_file_t *pktfd;
    apr_finfo_t finfo;
    apr_status_t rv;
    char errmsg[120];

    // open the file and get the file size
    rv = apr_file_open(&pktfd, pfile, APR_READ, APR_OS_DEFAULT, cntxt);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "wb: Could not open PKT data file (%s): %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }
    rv = apr_file_info_get(&finfo, APR_FINFO_NORM, pktfd);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "wb: Could not stat PKT data file (%s): %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }

    // allocate memeory for g_pkt_data to hold the entire file
    g_pkt_length = (apr_size_t)finfo.size;
    if (g_pkt_length <= 0) {
        fprintf(stderr, "wb: packets file(%s) is empty!\n", pfile);
        apr_file_close(pktfd);
        goto err_exit;
    }
    
    if (g_pkt_data) free(g_pkt_data);
    g_pkt_data = xmalloc(g_pkt_length);
    memset(g_pkt_data, 0, g_pkt_length);

    // read pkt file entirely into memory (g_pkt_data) and then close
    rv = apr_file_read_full(pktfd, g_pkt_data, g_pkt_length, NULL);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "wb: Could not read PKT data file: %s\n",
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }
    apr_file_close(pktfd);

    // now processing those packets, and get the packets number 
    // First, malloc space for pkt array to save the starting pointer of those sent packets
    if (g_MAX_PKT_COUNT == 0) // parse the packets string to get their count
        g_MAX_PKT_COUNT = parse_pktfile(g_pkt_data, NULL);
    
    if (g_MAX_PKT_COUNT == 0) {
        fprintf(stderr, "wb: packets file(%s) is invalid!\n", pfile);
        goto err_exit;
    }

    // allocate packet array memory and parse the packets again to save them
    g_pkt_array = xcalloc(g_MAX_PKT_COUNT, sizeof(struct _g_pkt_array_));
    g_pkt_count = parse_pktfile(g_pkt_data, g_pkt_array);
    //sort pkt by time
    if (g_pkt_count > 1) {
        qsort(g_pkt_array, g_pkt_count, sizeof(struct _g_pkt_array_), compare_pkt_by_time_to_send);
    }
    if (g_pkt_count > 1)
        nolength = 1; // no constant packet length if g_pkt_count >= 2

    return APR_SUCCESS;
    
err_exit:
    fprintf(stderr, "Error: wrong packet file (%s)!\n", pfile);
    if (g_pkt_data) free(g_pkt_data);
    exit (1);
} // end of open_pktfile

/* parse the packet strings */
static ulong parse_pktfile(char *pkt_data, struct _g_pkt_array_ *pkt_array)
{
    ulong pkt_count = 0;
    apr_size_t parsed_bytes = 0;
    char *p = pkt_data, *p2 = pkt_data, *p_digits;
    struct _g_pkt_array_ _pkt, *pkt;

    /*
     * if it starts with a NUMBER, it consists of multiple packets
     * if not, it's raw HTTP packet, (http methods at the beginning)
     * but we can still use '\0' for seperating multiple packets
     */
    if ( *p < '0' || *p > '9' ) { // not a digit
        // this is raw http packet, save them to pkt_array directly 
        parsed_bytes = 0;
        do { 
            if (pkt_array) 
                pkt = &pkt_array[pkt_count];
            else
                pkt = &_pkt;
            
            // save the start pointer of each packet
            pkt->pkt_data = pkt_data + parsed_bytes;
            // move to next packet by increment pkt_count
            // '\0' is seperator, use strlen to get the position of next packet
            pkt->pkt_length = strlen(pkt->pkt_data);

            // remove '\0' by +1
            parsed_bytes += pkt->pkt_length + 1;
            if (pkt->pkt_length < 4){
                if (!pkt_array && pkt->pkt_data[0] != '\0' && pkt->pkt_data[0] != '\r' && pkt->pkt_data[0] != '\n' ) 
                    fprintf(stderr, "Warning: this packet (%s) does not have a valid packet size(%d), ignore it!\n", 
                            pkt->pkt_data,pkt->pkt_length);
            }
                
            else 
                pkt_count ++;
        } while (parsed_bytes < g_pkt_length && (pkt_count < g_MAX_PKT_COUNT || g_MAX_PKT_COUNT == 0));

    } else { // chunked file, each packet has a PKT_SIZE number in the first line   
        parsed_bytes = 0;
        ulong l_pkt_size = 0;
		long time_sec, time_usec;
		char c;
        do {
			/*
            //  p points to first non-space char, skip the leading space
            while (parsed_bytes < g_pkt_length && apr_isspace(*p)) {
                p++;
                parsed_bytes ++;
            }
            
            // p_digits points to first non-digit char to fetch the digits for packet size; 
            p_digits = p; 
            while (parsed_bytes < g_pkt_length  && *p_digits >= '0' && *p_digits <= '9') {
                p_digits++;
                parsed_bytes ++;
            }

            if ( parsed_bytes >= g_pkt_length ) // end of file
                break; 
            
            // it's wrong if it does not have such digits and file does not end
            if ( p_digits == p) {
                fprintf(stderr, "Error: packets file does not have a valid packet size (%s)!\n", p);
                return 0;
            }
            
            *p_digits = 0; // so we can use string functions

            // end the processing if reads a "0"
            if ( (l_pkt_size = atoi(p)) <= 0)
                break;

            // skip the ending space,  starting from end of number
            parsed_bytes ++;
            p = p_digits + 1;
            //  p points to first non-CRLN char
            while (parsed_bytes < g_pkt_length && apr_isspace(*p)) {
                p++;
                parsed_bytes ++;
            }
            */

			// get the line feed and make it a c-based string
			for (p2 = p; *p2 && *p2 != '\r' && *p2 != '\n'; p2++);
			if (!*p2)
				break;
			c = *p2; 
			*p2 = 0;
			// use string scanf to fetch numbers
			sscanf(p,"%lu %lu.%lu",&l_pkt_size, &time_sec, &time_usec);
			*p2 = c;

			if (l_pkt_size > 0) {
	            // save the start pointer of each packet
	            if (pkt_array) 
	                pkt = &pkt_array[pkt_count];
	            else
	                pkt = &_pkt;
				for (p=p2+1; *p && apr_isspace(*p); p++);
	            
	            pkt->pkt_data = p;
	            pkt->pkt_length = l_pkt_size;
				pkt->pkt_time_to_send = time_sec * 1000000 + time_usec;

				parsed_bytes = p - g_pkt_data;

	            // move to next packet by increment pkt_count
	            // use l_pkt_size to get the position of next packet
	            parsed_bytes += l_pkt_size;

	            if ( parsed_bytes > g_pkt_length ) {// end of file, wrong!
	                fprintf(stderr, "Error: packets file needs a body (%s)!\n", p);
	                return 0;
	            }
	            
	            pkt_count ++;
				for (p = p + l_pkt_size; *p && apr_isspace(*p); p++);
			}
        } while (l_pkt_size > 0 && *p && (pkt_count < g_MAX_PKT_COUNT || g_MAX_PKT_COUNT == 0));
    }
    return pkt_count;
} // end of parse_pktfile 


/* open the file, and return the file handle in the parameter */
static apr_status_t open_file_for_write(const char * filename, apr_file_t **fd)
{ // -R/-g option.
    apr_status_t rv;
    char errmsg[120];
    rv = apr_file_open(fd, filename, 
        APR_FOPEN_CREATE | APR_FOPEN_WRITE | APR_FOPEN_TRUNCATE, 
        APR_OS_DEFAULT, cntxt);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "wb: Could not open file for write(%s): %s\n", filename,
                apr_strerror(rv, errmsg, sizeof errmsg));
    }                   
    return rv;
} // end of open_file_for_write

static int parse_opt_string(char *opt_string, char **myargv)
{
    if (!opt_string ||!*opt_string)
        return 0; 
    char *p, *line;
    int myargc = 1; // let myargv store args from [1]
    
    p = opt_string;
    while (*p){
        myargv[myargc++] = p;

        // find the ending '\r' or '\n'
        for (line = p; *line && *line != '\r' && *line != '\n'; line++);

        // move to the next line
        p = line; 

        if (*p && *p == '\r' && *(p+1) == '\n') {
            *p = 0;
            p++;
        }
        *p = '\0'; // mark this end;
        p ++;

    } // end of processing opt_string

    return (myargc - 1);
} // end of parse_opt_string

// read wb options(URL) from ini file
static apr_status_t read_inifile(const char *pfile, char *opt_string)
{
    apr_file_t *inifd;
    apr_finfo_t finfo;
    apr_status_t rv;
    char errmsg[120];
    apr_size_t filelen;
    char *ini_filename=(char *)pfile;

    // if no filename is specified, use default one "wb.ini"
    if (!pfile || !*pfile) 
        ini_filename = INI_FILENAME;
    
    
    rv = apr_file_open(&inifd, ini_filename, APR_READ, APR_OS_DEFAULT, cntxt);
    if (rv != APR_SUCCESS) {
        if (pfile)
            fprintf(stderr, "wb: Could not open ini file (%s) for read: %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }

    rv = apr_file_info_get(&finfo, APR_FINFO_NORM, inifd);
    if (rv != APR_SUCCESS) {
        if (pfile)
            fprintf(stderr, "wb: Could not stat ini file (%s): %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }
    filelen = (apr_size_t)finfo.size;
    rv = apr_file_read_full(inifd, opt_string, filelen, NULL);
    if (rv != APR_SUCCESS) {
        if (pfile)
            fprintf(stderr, "wb: Could not read ini file: %s\n",
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }

    apr_file_close(inifd);
    return APR_SUCCESS;
} // end of read_inifile

// write wb options(URL) to ini file
static apr_status_t write_inifile(const char *pfile,  int argc, char **argv)
{
    apr_file_t *inifd;
    apr_finfo_t finfo;
    apr_status_t rv;
    char errmsg[120];
    char *ini_filename=(char *)pfile;
    int i;

    // if no filename is specified, use default one "wb.ini"
    if (!pfile || !*pfile) 
        ini_filename = INI_FILENAME;
    
    rv = apr_file_open(&inifd, ini_filename, APR_WRITE|APR_CREATE|APR_TRUNCATE, APR_OS_DEFAULT, cntxt);
    if (rv != APR_SUCCESS) {
        if (pfile)
            fprintf(stderr, "wb: Could not open ini file(%s) for write: %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }

    for (i = 1; i < argc; i ++){
        if (strncmp((char *)argv[i], "-E", 2) == 0) {
            i++;
            continue;
        }
        if (strncmp((char *)argv[i], "-O", 2) == 0) {
            i++;
            continue;
        }
        if (strncmp((char *)argv[i], "-0", 2) == 0) {
            continue;
        }
        apr_fprintf(inifd, (char *)argv[i]);
        apr_fprintf(inifd, "\n");
    }
    
    apr_file_close(inifd);
    return APR_SUCCESS;
} // end of write_inifile

// save received http messages to log file
void save_logfile (char * buf, apr_size_t buflen)   
{
    apr_status_t rv;
    char errmsg[120];
    char size_str[128];
    static int need_add_LN = 0;
    
    apr_size_t need_save_length = buflen;
    apr_size_t saved_len = 0;
    apr_size_t next_save_length;

    if (!g_save_file_fd) {
        return;
    }

    // if exceeding max file size, rewind it to the beginning
    g_saved_bytes += need_save_length;
    if (g_MAX_FILE_SIZE > 0 && g_saved_bytes >= g_MAX_FILE_SIZE) {
        apr_off_t pos = 0;
        apr_file_seek(g_save_file_fd, APR_SET, &pos);
        g_saved_bytes = need_save_length;
    }

    // buf == NULL means writing the ending "0" to log file
    if (buf) {
        if (buflen == 0)
            buflen = strlen(buf);
        if (!buflen)
            return;
    } else
        buflen = 0;
    
    if (need_add_LN) {
        sprintf(size_str,"\n%zu\n",buflen);
    } else 
        sprintf(size_str,"%zu\n",buflen);
    
    next_save_length = strlen(size_str);
    rv = apr_file_write(g_save_file_fd, size_str, &next_save_length);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "wb: Could not write response size to output file: %s\n", 
                apr_strerror(rv, errmsg, sizeof errmsg));
        exit(1);
    }
    
    // make sure we save all need_save_length to output file
    need_save_length = buflen;
    saved_len = 0;  
    do {
        next_save_length = need_save_length - saved_len;
        rv = apr_file_write(g_save_file_fd, buf + saved_len, &next_save_length);
        if (rv != APR_SUCCESS) {
            fprintf(stderr, "wb: Could not write output file: %s\n", 
                    apr_strerror(rv, errmsg, sizeof errmsg));
            exit(1);
        }
        saved_len += next_save_length;
    }while (saved_len < need_save_length);

    if (buf && buflen > 0)
        need_add_LN = !(buf[buflen - 1] == '\n');
} // end of save_logfile: file to save received http messages

#endif //_WAF_BENCH_ // functions definitions

static void write_request(struct connection * c)
{
    if (started >= requests) {
        return;
    }

    do {
        apr_time_t tnow;
        apr_size_t l = c->rwrite;
        apr_status_t e = APR_SUCCESS; /* prevent gcc warning */

        tnow = lasttime = apr_time_now();

        /*
         * First time round ?
         */
        if (c->rwrite == 0) {
#ifdef _WAF_BENCH_ //  "-F" a packet file to be sent, 
            // Need write request, get the packet to be sent
            // g_pkt_length > 0 means the packet file is loaded
            // packet content is also loaded to g_pkt_array
            // might be merged to connection's members to support multi-thread
            if (g_pkt_length) {
		        static apr_time_t start_time_new_round;
                int pkt_id = get_write_pkt_id(c->socknum);
				if (pkt_id == 0)
					start_time_new_round = apr_time_now() - g_pkt_array[0].pkt_time_to_send;
                request = g_pkt_array[pkt_id].pkt_data;
                reqlen = g_pkt_array[pkt_id].pkt_length;
				while  (apr_time_now() < start_time_new_round+ g_pkt_array[pkt_id].pkt_time_to_send)
	                 apr_sleep(1);
            } 

            int hdr_delim = 0;
            int header_len = 0;
            
            if (g_add_connection_close || g_opt_prefix || g_sub_string_num) {  // packet need to be modify
                static ulong req_sent = 0;

                // keep original request length when adding seq#
                // since later on reqlen will be changed
                if (!g_pkt_length) { 
                    static int original_reqlen;
                    if (!req_sent) 
                        original_reqlen = reqlen;
                    else
                        reqlen = original_reqlen;
                }

                char req_id_string[1024]; // normally len of id string < 1024
                int req_id_string_len = 0;
                sprintf(req_id_string, "%lu",req_sent++);
                req_id_string_len = strlen(req_id_string);

                g_new_header_len = 0;
                g_new_header[0] = '\0';
                g_request_end = NULL;

                char *request_pos; // use this as processing position of request
                char *new_pos = NULL;

                request_pos = request; // start position of request
                if (g_opt_prefix) {// prepare the URL prefix string and its length
                    int method_length = 0;
                    // find the position in request header for URL:[SPACE]*METHOD[SPACE]+URL
                    // skip leading space
                    while (*request_pos && isspace(*request_pos)) request_pos++;
                    // skip the leading HTTP methods string
                    while (*request_pos && !isspace(*request_pos)) request_pos++;
                    // skip remaining space again
                    while (*request_pos && isspace(*request_pos))request_pos++;

                    method_length = request_pos - request;
                    if (!*request_pos && method_length < 4) 
                        fprintf(stderr, "Error! Request does not have a valid method:\n%s", request), exit(1);
                    
                    memcpy(g_new_header, request, method_length);
                    g_new_header[method_length] = 0;
                    strcat(g_new_header,"/");
                    strcat(g_new_header,g_opt_prefix);
                    strcat(g_new_header,req_id_string);
                    if (*request_pos != '/')
                        strcat(g_new_header,"/");
                    
                } // end of URL prefix

                // duplicate the whole request header
                // starting from URL position
                if (g_request_end = strstr(request_pos, "\r\n\r\n"))
                    hdr_delim = 4;
                /*
                 * this next line is so that we talk to NCSA 1.5 which blatantly
                 * breaks the http specifaction
                 */
                else if (g_request_end = strstr(request_pos, "\n\n")) 
                    hdr_delim = 2;
                else if (g_request_end = strstr(request_pos, "\r\r")) 
                    hdr_delim = 2;
                else {
                    fprintf(stderr, "Error! Request does not have a valid header(end with 2 LNs):\n%s", request);
                    exit(1);
                }
                    
                g_request_end += hdr_delim;


                // prepare the new header buffer
                int new_estimated_len;
                g_new_header_len = strlen(g_new_header);
                // assume each sub_string appears no than 10 times with less than 10-digits seq
                new_estimated_len = g_new_header_len + (g_request_end - request_pos) + reqlen + g_sub_string_num * 10 * 10 + 1;
                if (new_estimated_len > g_header_len_MAX) {
                    g_header_len_MAX = new_estimated_len; 
                    char *new_header;
                    new_header = xmalloc(g_header_len_MAX);
                    if (g_new_header) {
                        memcpy(new_header, g_new_header, g_new_header_len);
                        free(g_new_header);
                    }
                    g_new_header = new_header;
                }
                // copy the remaining header bytes  
                //memcpy(g_new_header + g_new_header_len, request_pos, g_request_end - request_pos );
                //g_new_header_len += g_request_end - request_pos ;

                // copy the remaining request bytes 
                header_len = g_new_header_len + g_request_end - request_pos - hdr_delim;
                memcpy(g_new_header + g_new_header_len, request_pos, request+reqlen - request_pos );
                g_new_header_len += (request + reqlen - request_pos) ;



                // mark its end so that we can use strstr
                g_new_header[g_new_header_len] = 0;
                char * new_request_end = g_new_header + g_new_header_len;

                // enumerate to process all sub_strings
                int i;
                for (i = 0; i < g_sub_string_num; i ++) {
                    char *sub;
                    while (sub = strstr(g_new_header, g_sub_string[i])) { 
                        if (sub - new_request_end > 0)
                            break;

                        char *copy_pos;
                        int copy_bytes;
                        int sub_len, j;

                        sub_len = strlen(g_sub_string[i]);
                        copy_pos = sub + sub_len;
                        copy_bytes = g_new_header_len-(copy_pos-g_new_header)+1;

                        if (sub_len > req_id_string_len)
                            for (j = 0; j < copy_bytes; j ++)
                                *(sub+req_id_string_len+j) = *(sub+sub_len+j);
                        else if (sub_len < req_id_string_len)
                            for (j = 0; j < copy_bytes; j ++)
                                *(sub+sub_len+j) = *(sub+req_id_string_len+j);
                        //memmove(sub+req_id_string_len, copy_pos, 
                        memcpy(sub, req_id_string, req_id_string_len);
                    }
                }
                g_new_header_len = strlen(g_new_header);
                //reqlen += g_new_header_len - (g_request_end - request);
                reqlen = g_new_header_len;

	            char *connection_hdr;
	            connection_hdr = strcasestr(g_new_header,"\r\nConnection:");
                if (connection_hdr == NULL) {
                    connection_hdr = strcasestr(g_new_header,"\n\nConnection:");
                }
                
                //if always connection:close, remove old connection:type
                if (g_add_connection_close == 2 && connection_hdr != NULL ) {
                    char * connection_hdr_end = strstr(connection_hdr + sizeof("\r\nConnection:") - 1, "\r\n");
                    if (connection_hdr_end == NULL) {
                        connection_hdr_end = strstr(connection_hdr + sizeof("\n\nConnection:") - 1, "\n\n");
                    }
                    
                    if (connection_hdr_end == NULL || connection_hdr_end > new_request_end) {
                        break;
                    }

                    int moved_bytes = g_new_header_len - (connection_hdr - g_new_header);
                    int j;

                    g_new_header_len = g_new_header_len - (connection_hdr_end - connection_hdr);
                    header_len = header_len - (connection_hdr_end - connection_hdr);

                    for (j = 0; j < moved_bytes; j++) {
                        *connection_hdr++ = *connection_hdr_end ++;
                    }
                    connection_hdr = NULL;
                }

	            // add connection:close header to the request
	            if (g_add_connection_close && (connection_hdr == NULL || connection_hdr >= new_request_end)) {
	                char conn_str[]="\r\nConnection: Close";
	                int conn_str_len = sizeof(conn_str) - 1;
	                char *dst = g_new_header+g_new_header_len+conn_str_len;
	                char *src = g_new_header+g_new_header_len;
	                int moved_bytes = g_new_header_len + 1 - header_len;
	                int j;

	                // move the data to get the space for connection string
	                for (j = 0; j < moved_bytes; j ++)
	                    *dst-- = *src --;

	                // now copy the connection string
	                memcpy(g_new_header + header_len, conn_str, conn_str_len);              
	                g_new_header_len = strlen(g_new_header);
	                //reqlen += g_new_header_len - (g_request_end - request);
	                reqlen = g_new_header_len;
	           }

            } // end of all prefix adding
#endif // _WAF_BENCH_ , "-F" a packet file to be sent, 

            apr_socket_timeout_set(c->aprsock, 0);
            c->connect = tnow;
            c->rwrote = 0;
            c->rwrite = reqlen;
            if (send_body)
                c->rwrite += postlen;
            l = c->rwrite;
        }
        else if (tnow > c->connect + aprtimeout) {
            printf("Send request timed out!\n");
            close_connection(c);
            return;
        }

#ifdef _WAF_BENCH_ // avoid copying post data to request
        // check whether it's time to send header from request
        // or it's time to send body from postdata with postlen
        // if c->rwrote <= reqlen, meaning it's header (request)
        // Otherwise, it's in body, so send postdata
        char *sendbuf; // point to the buffer to be sent

        if (c->rwrote < g_new_header_len) { // send prefix only
            sendbuf = g_new_header + c->rwrote;
            if (l > g_new_header_len - c->rwrote) 
                l = g_new_header_len - c->rwrote; 
        } else if (c->rwrote < reqlen) { // send request header
            // c->rwrote is the sent bytes, so start from there
            if (g_new_header_len && g_request_end)
                sendbuf = g_request_end + c->rwrote - g_new_header_len; 
            else
                sendbuf = request + c->rwrote;
            // and make sure it's not exceeding request buffer
            // because the remaining bytes are in body part
            if (l > reqlen - c->rwrote) 
                l = reqlen - c->rwrote; 
        } else  // send postdata, reqlen is already sent
            sendbuf = postdata + c->rwrote - reqlen;
        if (verbosity >= 2)
            printf("writing request(%zu bytes)=>[%s]\n",l, sendbuf);
#endif // _WAF_BENCH_ // avoid copying post data to request

#ifdef USE_SSL
        if (c->ssl) {
#ifdef _WAF_BENCH_ // avoid copying post data to request
            e = SSL_write(c->ssl, sendbuf, l);
#else
            e = SSL_write(c->ssl, request + c->rwrote, l);
#endif // _WAF_BENCH_ // avoid copying post data to request
            if (e <= 0) {
                switch (SSL_get_error(c->ssl, e)) {
                case SSL_ERROR_WANT_READ:
                    set_polled_events(c, APR_POLLIN);
                    break;
                case SSL_ERROR_WANT_WRITE:
                    set_polled_events(c, APR_POLLOUT);
                    break;
                default:
                    BIO_printf(bio_err, "SSL write failed - closing connection\n");
                    ERR_print_errors(bio_err);
                    close_connection (c);
                    break;
                }
                return;
            }
            l = e;
        }
        else
#endif
        {
#ifdef _WAF_BENCH_ // avoid copying post data to request
            e = apr_socket_send(c->aprsock, sendbuf, &l);
#else
            e = apr_socket_send(c->aprsock, request + c->rwrote, &l);
#endif // _WAF_BENCH_ // avoid copying post data to request
            if (e != APR_SUCCESS && !l) {
                if (!APR_STATUS_IS_EAGAIN(e)) {
                    epipe++;
                    printf("Send request failed!\n");
                    close_connection(c);
                }
                else {
                    set_polled_events(c, APR_POLLOUT);
                }
                return;
            }
        }
        totalposted += l;
        c->rwrote += l;
        c->rwrite -= l;
    } while (c->rwrite);

    c->endwrite = lasttime = apr_time_now();
    started++;
    set_conn_state(c, STATE_READ);
}

/* --------------------------------------------------------- */

/* calculate and output results */

static int compradre(struct data * a, struct data * b)
{
    if ((a->ctime) < (b->ctime))
        return -1;
    if ((a->ctime) > (b->ctime))
        return +1;
    return 0;
}

static int comprando(struct data * a, struct data * b)
{
    if ((a->time) < (b->time))
        return -1;
    if ((a->time) > (b->time))
        return +1;
    return 0;
}

static int compri(struct data * a, struct data * b)
{
    apr_interval_time_t p = a->time - a->ctime;
    apr_interval_time_t q = b->time - b->ctime;
    if (p < q)
        return -1;
    if (p > q)
        return +1;
    return 0;
}

static int compwait(struct data * a, struct data * b)
{
    if ((a->waittime) < (b->waittime))
        return -1;
    if ((a->waittime) > (b->waittime))
        return 1;
    return 0;
}

static void output_results(int sig)
{
    double timetaken;

    if (sig) {
        lasttime = apr_time_now();  /* record final time if interrupted */
    }
    timetaken = (double) (lasttime - start) / APR_USEC_PER_SEC;

    printf("\n\n");
    printf("Server Software:        %s\n", servername);
    printf("Server Hostname:        %s\n", hostname);
    printf("Server Port:            %hu\n", port);
#ifdef USE_SSL
    if (is_ssl && ssl_info) {
        printf("SSL/TLS Protocol:       %s\n", ssl_info);
    }
    if (is_ssl && ssl_tmp_key) {
        printf("Server Temp Key:        %s\n", ssl_tmp_key);
    }
#ifdef HAVE_TLSEXT
    if (is_ssl && tls_sni) {
        printf("TLS Server Name:        %s\n", tls_sni);
    }
#endif
#endif
    printf("\n");
    printf("Document Path:          %s\n", path);
    if (nolength)
        printf("Document Length:        Variable\n");
    else
        printf("Document Length:        %" APR_SIZE_T_FMT " bytes\n", doclen);
    printf("\n");
    printf("Concurrency Level:      %d\n", concurrency);
    printf("Time taken for tests:   %.3f seconds\n", timetaken);
    printf("Complete requests:      %d\n", done);

#ifdef _WAF_BENCH_ // print color text for bad results
    //if (bad > 0) 
        printf("\033[0;31m"); // RED color for failed requests
#endif //_WAF_BENCH_ print color text

    printf("Failed requests:        %d\n", bad);
    if (bad)
        printf("   (Connect: %d, Receive: %d, Length: %d, Exceptions: %d)\n",
            err_conn, err_recv, err_length, err_except);
    if (epipe)
        printf("Write errors:           %d\n", epipe);
    if (err_response)
        printf("Non-2xx responses:      %d\n", err_response);
#ifdef _WAF_BENCH_ // return to no-color
    //if (bad > 0) 
        printf("\033[0m"); // no color
#endif //_WAF_BENCH_ return to no-color
    if (keepalive)
        printf("Keep-Alive requests:    %d\n", doneka);
    printf("Total transferred:      %" APR_INT64_T_FMT " bytes\n", totalread);
    if (send_body)
        printf("Total body sent:        %" APR_INT64_T_FMT "\n",
               totalposted);
    printf("HTML transferred:       %" APR_INT64_T_FMT " bytes\n", totalbread);

    /* avoid divide by zero */
    if (timetaken && done) {
        
#ifdef _WAF_BENCH_ // print color text
        printf("\033[1;33m"); // Yellow color for RPS numbers
#endif //_WAF_BENCH_ print color text

        printf("Requests per second:    %.2f [#/sec] (mean)\n",
               (double) done / timetaken);
               
#ifdef _WAF_BENCH_ // print no-color text
        printf("\033[0m"); // no color
#endif //_WAF_BENCH_ print no-color text
        
        printf("Time per request:       %.3f [ms] (mean)\n",
               (double) concurrency * timetaken * 1000 / done);
#ifdef _WAF_BENCH_ // when concurrency == 1, we can avoid print duplicated results
        if (concurrency > 1)
#endif //_WAF_BENCH_ when concurrency == 1, we can avoid print duplicated results
        printf("Time per request:       %.3f [ms] (mean, across all concurrent requests)\n",
               (double) timetaken * 1000 / done);
        printf("Transfer rate:          %.2f [Kbytes/sec] received\n",
               (double) totalread / 1024 / timetaken);
        if (send_body) {
            printf("                        %.2f kb/s sent\n",
               (double) totalposted / 1024 / timetaken);
            printf("                        %.2f kb/s total\n",
               (double) (totalread + totalposted) / 1024 / timetaken);
        }
    }

#ifdef _WAF_BENCH_ // real sent# might be greater than g_stats_window;
    done = ap_min(done, g_stats_window);
    printf("Total samples of stats: %d",done);
#endif //_WAF_BENCH_ real sent# might be greater than g_stats_window;

    if (done > 0) {
        /* work out connection times */
        int i;
        apr_time_t totalcon = 0, total = 0, totald = 0, totalwait = 0;
        apr_time_t meancon, meantot, meand, meanwait;
        apr_interval_time_t mincon = AB_MAX, mintot = AB_MAX, mind = AB_MAX,
                            minwait = AB_MAX;
        apr_interval_time_t maxcon = 0, maxtot = 0, maxd = 0, maxwait = 0;
        apr_interval_time_t mediancon = 0, mediantot = 0, mediand = 0, medianwait = 0;
        double sdtot = 0, sdcon = 0, sdd = 0, sdwait = 0;

        for (i = 0; i < done; i++) {
            struct data *s = &stats[i];
            mincon = ap_min(mincon, s->ctime);
            mintot = ap_min(mintot, s->time);
            mind = ap_min(mind, s->time - s->ctime);
            minwait = ap_min(minwait, s->waittime);

            maxcon = ap_max(maxcon, s->ctime);
            maxtot = ap_max(maxtot, s->time);
            maxd = ap_max(maxd, s->time - s->ctime);
            maxwait = ap_max(maxwait, s->waittime);

            totalcon += s->ctime;
            total += s->time;
            totald += s->time - s->ctime;
            totalwait += s->waittime;
        }
        meancon = totalcon / done;
        meantot = total / done;
        meand = totald / done;
        meanwait = totalwait / done;

        /* calculating the sample variance: the sum of the squared deviations, divided by n-1 */
        for (i = 0; i < done; i++) {
            struct data *s = &stats[i];
            double a;
            a = ((double)s->time - meantot);
            sdtot += a * a;
            a = ((double)s->ctime - meancon);
            sdcon += a * a;
            a = ((double)s->time - (double)s->ctime - meand);
            sdd += a * a;
            a = ((double)s->waittime - meanwait);
            sdwait += a * a;
        }

        sdtot = (done > 1) ? sqrt(sdtot / (done - 1)) : 0;
        sdcon = (done > 1) ? sqrt(sdcon / (done - 1)) : 0;
        sdd = (done > 1) ? sqrt(sdd / (done - 1)) : 0;
        sdwait = (done > 1) ? sqrt(sdwait / (done - 1)) : 0;

        /*
         * XXX: what is better; this hideous cast of the compradre function; or
         * the four warnings during compile ? dirkx just does not know and
         * hates both/
         */
        qsort(stats, done, sizeof(struct data),
              (int (*) (const void *, const void *)) compradre);
        if ((done > 1) && (done % 2))
            mediancon = (stats[done / 2].ctime + stats[done / 2 + 1].ctime) / 2;
        else
            mediancon = stats[done / 2].ctime;

        qsort(stats, done, sizeof(struct data),
              (int (*) (const void *, const void *)) compri);
        if ((done > 1) && (done % 2))
            mediand = (stats[done / 2].time + stats[done / 2 + 1].time \
            -stats[done / 2].ctime - stats[done / 2 + 1].ctime) / 2;
        else
            mediand = stats[done / 2].time - stats[done / 2].ctime;

        qsort(stats, done, sizeof(struct data),
              (int (*) (const void *, const void *)) compwait);
        if ((done > 1) && (done % 2))
            medianwait = (stats[done / 2].waittime + stats[done / 2 + 1].waittime) / 2;
        else
            medianwait = stats[done / 2].waittime;

        qsort(stats, done, sizeof(struct data),
              (int (*) (const void *, const void *)) comprando);
        if ((done > 1) && (done % 2))
            mediantot = (stats[done / 2].time + stats[done / 2 + 1].time) / 2;
        else
            mediantot = stats[done / 2].time;
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
        if (g_us_granularity)
            printf("\nConnection Times (us)\n");            
        else {
#endif // _WAF_BENCH_ // microsec-granularity in output-results
            
        printf("\nConnection Times (ms)\n");
        /*
         * Reduce stats from apr time to milliseconds
         */
        mincon     = ap_round_ms(mincon);
        mind       = ap_round_ms(mind);
        minwait    = ap_round_ms(minwait);
        mintot     = ap_round_ms(mintot);
        meancon    = ap_round_ms(meancon);
        meand      = ap_round_ms(meand);
        meanwait   = ap_round_ms(meanwait);
        meantot    = ap_round_ms(meantot);
        mediancon  = ap_round_ms(mediancon);
        mediand    = ap_round_ms(mediand);
        medianwait = ap_round_ms(medianwait);
        mediantot  = ap_round_ms(mediantot);
        maxcon     = ap_round_ms(maxcon);
        maxd       = ap_round_ms(maxd);
        maxwait    = ap_round_ms(maxwait);
        maxtot     = ap_round_ms(maxtot);
        sdcon      = ap_double_ms(sdcon);
        sdd        = ap_double_ms(sdd);
        sdwait     = ap_double_ms(sdwait);
        sdtot      = ap_double_ms(sdtot);

#ifdef _WAF_BENCH_ // microsec-granularity in output-results
        }
#endif // _WAF_BENCH_ // microsec-granularity in output-results
        if (confidence) {
#define CONF_FMT_STRING "%5" APR_TIME_T_FMT " %4" APR_TIME_T_FMT " %5.1f %6" APR_TIME_T_FMT " %7" APR_TIME_T_FMT "\n"
            printf("              min  mean[+/-sd] median   max\n");
            printf("Connect:    " CONF_FMT_STRING,
                   mincon, meancon, sdcon, mediancon, maxcon);
            printf("Processing: " CONF_FMT_STRING,
                   mind, meand, sdd, mediand, maxd);
            printf("Waiting:    " CONF_FMT_STRING,
                   minwait, meanwait, sdwait, medianwait, maxwait);
            printf("Total:      " CONF_FMT_STRING,
                   mintot, meantot, sdtot, mediantot, maxtot);
#undef CONF_FMT_STRING

#define     SANE(what,mean,median,sd) \
              { \
                double d = (double)mean - median; \
                if (d < 0) d = -d; \
                if (d > 2 * sd ) \
                    printf("ERROR: The median and mean for " what " are more than twice the standard\n" \
                           "       deviation apart. These results are NOT reliable.\n"); \
                else if (d > sd ) \
                    printf("WARNING: The median and mean for " what " are not within a normal deviation\n" \
                           "        These results are probably not that reliable.\n"); \
            }
            SANE("the initial connection time", meancon, mediancon, sdcon);
            SANE("the processing time", meand, mediand, sdd);
            SANE("the waiting time", meanwait, medianwait, sdwait);
            SANE("the total time", meantot, mediantot, sdtot);
        }
        else {
            printf("              min   avg   max\n");
#define CONF_FMT_STRING "%5" APR_TIME_T_FMT " %5" APR_TIME_T_FMT "%5" APR_TIME_T_FMT "\n"
            printf("Connect:    " CONF_FMT_STRING, mincon, meancon, maxcon);
            printf("Processing: " CONF_FMT_STRING, mind, meand, maxd);
            printf("Waiting:    " CONF_FMT_STRING, minwait, meanwait, maxwait);
            printf("Total:      " CONF_FMT_STRING, mintot, meantot, maxtot);
#undef CONF_FMT_STRING
        }


        /* Sorted on total connect times */
        if (percentile && (done > 1)) {
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
            if (g_us_granularity)
            printf("\nPercentage of the requests served within a certain time (us)\n");
            else
#endif // _WAF_BENCH_ // microsec-granularity in output-results
            printf("\nPercentage of the requests served within a certain time (ms)\n");
            for (i = 0; i < sizeof(percs) / sizeof(int); i++) {
                if (percs[i] <= 0)
                    printf(" 0%%  <0> (never)\n");
                else if (percs[i] >= 100)
                    printf(" 100%%  %5" APR_TIME_T_FMT " (longest request)\n",
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                    g_us_granularity?stats[done - 1].time:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                           ap_round_ms(stats[done - 1].time));
                else
                    printf("  %d%%  %5" APR_TIME_T_FMT "\n", percs[i],
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                        g_us_granularity?stats[(unsigned long)done * percs[i] / 100].time:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                           ap_round_ms(stats[(unsigned long)done * percs[i] / 100].time));
            }
        }
        if (csvperc) {
            FILE *out = fopen(csvperc, "w");
            if (!out) {
                perror("Cannot open CSV output file");
                exit(1);
            }
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
            if (g_us_granularity)
            fprintf(out, "" "Percentage served" "," "Time in us" "\n");
            else
#endif // _WAF_BENCH_ // microsec-granularity in output-results
            fprintf(out, "" "Percentage served" "," "Time in ms" "\n");             
            for (i = 0; i <= 100; i++) {
                double t;
                if (i == 0)
                    t = ap_double_ms(stats[0].time);
                else if (i == 100)
                    t = ap_double_ms(stats[done - 1].time);
                else
                    t = ap_double_ms(stats[(unsigned long) (0.5 + (double)done * i / 100.0)].time);
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
            if (g_us_granularity)
                t = t * 1000; // convert back to us             
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                fprintf(out, "%d,%.3f\n", i, t);
            }
            fclose(out);
        }
        if (gnuplot) {
            FILE *out = fopen(gnuplot, "w");
            char tmstring[APR_CTIME_LEN];
            if (!out) {
                perror("Cannot open gnuplot output file");
                exit(1);
            }
            fprintf(out, "starttime\tseconds\tctime\tdtime\tttime\twait\n");
            for (i = 0; i < done; i++) {
                (void) apr_ctime(tmstring, stats[i].starttime);
                fprintf(out, "%s\t%" APR_TIME_T_FMT "\t%" APR_TIME_T_FMT
                               "\t%" APR_TIME_T_FMT "\t%" APR_TIME_T_FMT
                               "\t%" APR_TIME_T_FMT "\n", tmstring,
                        apr_time_sec(stats[i].starttime),
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                        g_us_granularity?stats[i].ctime:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                        ap_round_ms(stats[i].ctime),
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                        g_us_granularity?stats[i].time - stats[i].ctime:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                        ap_round_ms(stats[i].time - stats[i].ctime),
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                        g_us_granularity?stats[i].time:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                        ap_round_ms(stats[i].time),
#ifdef _WAF_BENCH_ // microsec-granularity in output-results
                        g_us_granularity?stats[i].waittime:
#endif // _WAF_BENCH_ // microsec-granularity in output-results
                        ap_round_ms(stats[i].waittime));
            }
            fclose(out);
        }
    }

    if (sig) {
        exit(1);
    }
}

/* --------------------------------------------------------- */

/* calculate and output results in HTML  */

static void output_html_results(void)
{
    double timetaken = (double) (lasttime - start) / APR_USEC_PER_SEC;

    printf("\n\n<table %s>\n", tablestring);
    printf("<tr %s><th colspan=2 %s>Server Software:</th>"
       "<td colspan=2 %s>%s</td></tr>\n",
       trstring, tdstring, tdstring, servername);
    printf("<tr %s><th colspan=2 %s>Server Hostname:</th>"
       "<td colspan=2 %s>%s</td></tr>\n",
       trstring, tdstring, tdstring, hostname);
    printf("<tr %s><th colspan=2 %s>Server Port:</th>"
       "<td colspan=2 %s>%hu</td></tr>\n",
       trstring, tdstring, tdstring, port);
    printf("<tr %s><th colspan=2 %s>Document Path:</th>"
       "<td colspan=2 %s>%s</td></tr>\n",
       trstring, tdstring, tdstring, path);
    if (nolength)
        printf("<tr %s><th colspan=2 %s>Document Length:</th>"
            "<td colspan=2 %s>Variable</td></tr>\n",
            trstring, tdstring, tdstring);
    else
        printf("<tr %s><th colspan=2 %s>Document Length:</th>"
            "<td colspan=2 %s>%" APR_SIZE_T_FMT " bytes</td></tr>\n",
            trstring, tdstring, tdstring, doclen);
    printf("<tr %s><th colspan=2 %s>Concurrency Level:</th>"
       "<td colspan=2 %s>%d</td></tr>\n",
       trstring, tdstring, tdstring, concurrency);
    printf("<tr %s><th colspan=2 %s>Time taken for tests:</th>"
       "<td colspan=2 %s>%.3f seconds</td></tr>\n",
       trstring, tdstring, tdstring, timetaken);
    printf("<tr %s><th colspan=2 %s>Complete requests:</th>"
       "<td colspan=2 %s>%d</td></tr>\n",
       trstring, tdstring, tdstring, done);
    printf("<tr %s><th colspan=2 %s>Failed requests:</th>"
       "<td colspan=2 %s>%d</td></tr>\n",
       trstring, tdstring, tdstring, bad);
    if (bad)
        printf("<tr %s><td colspan=4 %s >   (Connect: %d, Length: %d, Exceptions: %d)</td></tr>\n",
           trstring, tdstring, err_conn, err_length, err_except);
    if (err_response)
        printf("<tr %s><th colspan=2 %s>Non-2xx responses:</th>"
           "<td colspan=2 %s>%d</td></tr>\n",
           trstring, tdstring, tdstring, err_response);
    if (keepalive)
        printf("<tr %s><th colspan=2 %s>Keep-Alive requests:</th>"
           "<td colspan=2 %s>%d</td></tr>\n",
           trstring, tdstring, tdstring, doneka);
    printf("<tr %s><th colspan=2 %s>Total transferred:</th>"
       "<td colspan=2 %s>%" APR_INT64_T_FMT " bytes</td></tr>\n",
       trstring, tdstring, tdstring, totalread);
    if (send_body)
        printf("<tr %s><th colspan=2 %s>Total body sent:</th>"
           "<td colspan=2 %s>%" APR_INT64_T_FMT "</td></tr>\n",
           trstring, tdstring,
           tdstring, totalposted);
    printf("<tr %s><th colspan=2 %s>HTML transferred:</th>"
       "<td colspan=2 %s>%" APR_INT64_T_FMT " bytes</td></tr>\n",
       trstring, tdstring, tdstring, totalbread);

    /* avoid divide by zero */
    if (timetaken) {
        printf("<tr %s><th colspan=2 %s>Requests per second:</th>"
           "<td colspan=2 %s>%.2f</td></tr>\n",
           trstring, tdstring, tdstring, (double) done / timetaken);
        printf("<tr %s><th colspan=2 %s>Transfer rate:</th>"
           "<td colspan=2 %s>%.2f kb/s received</td></tr>\n",
           trstring, tdstring, tdstring, (double) totalread / 1024 / timetaken);
        if (send_body) {
            printf("<tr %s><td colspan=2 %s>&nbsp;</td>"
               "<td colspan=2 %s>%.2f kb/s sent</td></tr>\n",
               trstring, tdstring, tdstring,
               (double) totalposted / 1024 / timetaken);
            printf("<tr %s><td colspan=2 %s>&nbsp;</td>"
               "<td colspan=2 %s>%.2f kb/s total</td></tr>\n",
               trstring, tdstring, tdstring,
               (double) (totalread + totalposted) / 1024 / timetaken);
        }
    }
    {
#ifdef _WAF_BENCH_ // real sent# might be greater than MAX_REQUEST;
        done = ap_min(done, g_stats_window);
#endif //_WAF_BENCH_ real sent# might be greater than MAX_REQUEST;

        /* work out connection times */
        int i;
        apr_interval_time_t totalcon = 0, total = 0;
        apr_interval_time_t mincon = AB_MAX, mintot = AB_MAX;
        apr_interval_time_t maxcon = 0, maxtot = 0;

        for (i = 0; i < done; i++) {
            struct data *s = &stats[i];
            mincon = ap_min(mincon, s->ctime);
            mintot = ap_min(mintot, s->time);
            maxcon = ap_max(maxcon, s->ctime);
            maxtot = ap_max(maxtot, s->time);
            totalcon += s->ctime;
            total    += s->time;
        }
        /*
         * Reduce stats from apr time to milliseconds
         */
        mincon   = ap_round_ms(mincon);
        mintot   = ap_round_ms(mintot);
        maxcon   = ap_round_ms(maxcon);
        maxtot   = ap_round_ms(maxtot);
        totalcon = ap_round_ms(totalcon);
        total    = ap_round_ms(total);

        if (done > 0) { /* avoid division by zero (if 0 done) */
            printf("<tr %s><th %s colspan=4>Connnection Times (ms)</th></tr>\n",
               trstring, tdstring);
            printf("<tr %s><th %s>&nbsp;</th> <th %s>min</th>   <th %s>avg</th>   <th %s>max</th></tr>\n",
               trstring, tdstring, tdstring, tdstring, tdstring);
            printf("<tr %s><th %s>Connect:</th>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td></tr>\n",
               trstring, tdstring, tdstring, mincon, tdstring, totalcon / done, tdstring, maxcon);
            printf("<tr %s><th %s>Processing:</th>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td></tr>\n",
               trstring, tdstring, tdstring, mintot - mincon, tdstring,
               (total / done) - (totalcon / done), tdstring, maxtot - maxcon);
            printf("<tr %s><th %s>Total:</th>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td>"
               "<td %s>%5" APR_TIME_T_FMT "</td></tr>\n",
               trstring, tdstring, tdstring, mintot, tdstring, total / done, tdstring, maxtot);
        }
        printf("</table>\n");
    }
}

/* --------------------------------------------------------- */

/* start asnchronous non-blocking connection */

static void start_connect(struct connection * c)
{
    apr_status_t rv;

    if (!(started < requests))
        return;

#ifdef _WAF_BENCH_ // make sure not exceeding RPS limit
	static int connection_rps_banned = 0;
    if  (g_RPS_NUMBER > 0 && done > (g_RPS_NUMBER * (apr_time_now() - start) / APR_USEC_PER_SEC )) {
		connection_rps_banned ++;

		// ban the connect if it exceeds RPS now
		if (connection_rps_banned < concurrency) 
			return;

		// if all connections are banned, wait for timeout
	    while  (g_RPS_NUMBER > 0 && done > (g_RPS_NUMBER * (apr_time_now() - start) / APR_USEC_PER_SEC ))
	            apr_sleep(1);

		// restart all connections
		connection_rps_banned = 0;
		int i;
        for (i = 0; i < concurrency; i++) 
            start_connect(&con[i]);
    }
#endif //_WAF_BENCH_ // // make sure not exceeding RPS limit

    c->read = 0;
    c->bread = 0;
    c->keepalive = 0;
    c->cbx = 0;
    c->gotheader = 0;
    c->rwrite = 0;
    if (c->ctx)
        apr_pool_clear(c->ctx);
    else
        apr_pool_create(&c->ctx, cntxt);

    if ((rv = apr_socket_create(&c->aprsock, destsa->family,
                SOCK_STREAM, 0, c->ctx)) != APR_SUCCESS) {
    apr_err("socket", rv);
    }

    if (myhost) {
        if ((rv = apr_socket_bind(c->aprsock, mysa)) != APR_SUCCESS) {
            apr_err("bind", rv);
        }
    }

    c->pollfd.desc_type = APR_POLL_SOCKET;
    c->pollfd.desc.s = c->aprsock;
    c->pollfd.reqevents = 0;
    c->pollfd.client_data = c;

    if ((rv = apr_socket_opt_set(c->aprsock, APR_SO_NONBLOCK, 1))
         != APR_SUCCESS) {
        apr_err("socket nonblock", rv);
    }

    if (windowsize != 0) {
        rv = apr_socket_opt_set(c->aprsock, APR_SO_SNDBUF,
                                windowsize);
        if (rv != APR_SUCCESS && rv != APR_ENOTIMPL) {
            apr_err("socket send buffer", rv);
        }
        rv = apr_socket_opt_set(c->aprsock, APR_SO_RCVBUF,
                                windowsize);
        if (rv != APR_SUCCESS && rv != APR_ENOTIMPL) {
            apr_err("socket receive buffer", rv);
        }
    }

    c->start = lasttime = apr_time_now();
#ifdef USE_SSL
    if (is_ssl) {
        BIO *bio;
        apr_os_sock_t fd;

        if ((c->ssl = SSL_new(ssl_ctx)) == NULL) {
            BIO_printf(bio_err, "SSL_new failed.\n");
            ERR_print_errors(bio_err);
            exit(1);
        }
        ssl_rand_seed();
        apr_os_sock_get(&fd, c->aprsock);
        bio = BIO_new_socket(fd, BIO_NOCLOSE);
        BIO_set_nbio(bio, 1);
        SSL_set_bio(c->ssl, bio, bio);
        SSL_set_connect_state(c->ssl);
        if (verbosity >= 4) {
            BIO_set_callback(bio, ssl_print_cb);
            BIO_set_callback_arg(bio, (void *)bio_err);
        }
#ifdef HAVE_TLSEXT
        if (tls_sni) {
            SSL_set_tlsext_host_name(c->ssl, tls_sni);
        }
#endif
    } else {
        c->ssl = NULL;
    }
#endif
    if ((rv = apr_socket_connect(c->aprsock, destsa)) != APR_SUCCESS) {
        if (APR_STATUS_IS_EINPROGRESS(rv)) {
            set_conn_state(c, STATE_CONNECTING);
            c->rwrite = 0;
            return;
        }
        else {
            set_conn_state(c, STATE_UNCONNECTED);
            apr_socket_close(c->aprsock);
            if (good == 0 && destsa->next) {
                destsa = destsa->next;
                err_conn = 0;
            }
            else if (bad++ > 10) {
                fprintf(stderr,
                   "\nTest aborted after 10 failures\n\n");
                apr_err("apr_socket_connect()", rv);
            }
            else {
                err_conn++;
            }

            start_connect(c);
            return;
        }
    }

    /* connected first time */
    set_conn_state(c, STATE_CONNECTED);
#ifdef USE_SSL
    if (c->ssl) {
        ssl_proceed_handshake(c);
    } else
#endif
    {
        write_request(c);
    }
}

/* --------------------------------------------------------- */

/* close down connection and save stats */

static void close_connection(struct connection * c)
{
    if (c->read == 0 && c->keepalive) {
        /*
         * server has legitimately shut down an idle keep alive request
         */
        if (good)
            good--;     /* connection never happened */
    }
    else {
        if (good == 1) {
            /* first time here */
            doclen = c->bread;
        }
        else if ((c->bread != doclen) && !nolength) {
            bad++;
            err_length++;
        }
        /* save out time */
        if (done < requests) {
#ifdef _WAF_BENCH_ // make sure not exceeding stats size
           struct data *s = &stats[(done++)%g_stats_window]; 
#else // original code goes here
            struct data *s = &stats[done++];
#endif //_WAF_BENCH_ // // make sure not exceeding stats size
            c->done      = lasttime = apr_time_now();
            s->starttime = c->start;
            s->ctime     = ap_max(0, c->connect - c->start);
            s->time      = ap_max(0, c->done - c->start);
            s->waittime  = ap_max(0, c->beginread - c->endwrite);
            if (heartbeatres && !(done % heartbeatres)) {
                fprintf(stderr, "Completed %d requests\n", done);
                fflush(stderr);
            }
        }
    }

    set_conn_state(c, STATE_UNCONNECTED);
#ifdef USE_SSL
    if (c->ssl) {
        SSL_shutdown(c->ssl);
        SSL_free(c->ssl);
        c->ssl = NULL;
    }
#endif
    apr_socket_close(c->aprsock);

    /* connect again */
    start_connect(c);
    return;
}

/* --------------------------------------------------------- */

/* read data from connection */

static void read_connection(struct connection * c)
{
    apr_size_t r;
    apr_status_t status;
    char *part;
    char respcode[4];       /* 3 digits and null */
    int i;

    r = sizeof(buffer);
read_more:
#ifdef USE_SSL
    if (c->ssl) {
        status = SSL_read(c->ssl, buffer, r);
        if (status <= 0) {
            int scode = SSL_get_error(c->ssl, status);

            if (scode == SSL_ERROR_ZERO_RETURN) {
                /* connection closed cleanly: */
                good++;
                close_connection(c);
            }
            else if (scode == SSL_ERROR_SYSCALL
                     && status == 0
                     && c->read != 0) {
                /* connection closed, but in violation of the protocol, after
                 * some data has already been read; this commonly happens, so
                 * let the length check catch any response errors
                 */
                good++;
                close_connection(c);
            }
            else if (scode == SSL_ERROR_SYSCALL 
                     && c->read == 0
                     && destsa->next
                     && c->state == STATE_CONNECTING
                     && good == 0) {
                return;
            }
            else if (scode == SSL_ERROR_WANT_READ) {
                set_polled_events(c, APR_POLLIN);
            }
            else if (scode == SSL_ERROR_WANT_WRITE) {
                set_polled_events(c, APR_POLLOUT);
            }
            else {
                /* some fatal error: */
                c->read = 0;
                BIO_printf(bio_err, "SSL read failed (%d) - closing connection\n", scode);
                ERR_print_errors(bio_err);
                close_connection(c);
            }
            return;
        }
        r = status;
    }
    else
#endif
    {
        status = apr_socket_recv(c->aprsock, buffer, &r);
        if (APR_STATUS_IS_EAGAIN(status))
            return;
        else if (r == 0 && APR_STATUS_IS_EOF(status)) {
            good++;
            close_connection(c);
            return;
        }
        /* catch legitimate fatal apr_socket_recv errors */
        else if (status != APR_SUCCESS) {
            if (recverrok) {
                err_recv++;
                bad++;
                close_connection(c);
                if (verbosity >= 1) {
                    char buf[120];
                    fprintf(stderr,"%s: %s (%d)\n", "apr_socket_recv", apr_strerror(status, buf, sizeof buf), status);
                }
                return;
            } else if (destsa->next && c->state == STATE_CONNECTING
                       && c->read == 0 && good == 0) {
                return;
            }
            else {
                err_recv++;
                apr_err("apr_socket_recv", status);
            }
        }
    }

    totalread += r;
    if (c->read == 0) {
        c->beginread = apr_time_now();
    }
#ifdef _WAF_BENCH_ // save packets to file
    if (g_save_file_fd) {
        //write "\n\n" as seperator of packets
        //if (c->read == 0) 
        //  apr_fprintf(g_save_file_fd, "\n\n");
        
        // if it's header, or we need save body, save it.
        if (!c->gotheader || g_save_body)
            save_logfile(buffer, r);
        if (verbosity >= 2) {
            printf("LOG: http packet received(%zu bytes):\n%s\n", r,buffer);
        }
    }
#endif //_WAF_BENCH_ , // save packets to file

    c->read += r;

    if (!c->gotheader) {
        char *s;
        int l = 4;
        apr_size_t space = CBUFFSIZE - c->cbx - 1; /* -1 allows for \0 term */
        int tocopy = (space < r) ? space : r;
#ifdef NOT_ASCII
        apr_size_t inbytes_left = space, outbytes_left = space;

        status = apr_xlate_conv_buffer(from_ascii, buffer, &inbytes_left,
                           c->cbuff + c->cbx, &outbytes_left);
        if (status || inbytes_left || outbytes_left) {
            fprintf(stderr, "only simple translation is supported (%d/%" APR_SIZE_T_FMT
                            "/%" APR_SIZE_T_FMT ")\n", status, inbytes_left, outbytes_left);
            exit(1);
        }
#else
        memcpy(c->cbuff + c->cbx, buffer, space);
#endif              /* NOT_ASCII */
        c->cbx += tocopy;
        space -= tocopy;
        c->cbuff[c->cbx] = 0;   /* terminate for benefit of strstr */
        if (verbosity >= 2) {
            printf("LOG: header received:\n%s\n", c->cbuff);
        }
        s = strstr(c->cbuff, "\r\n\r\n");
        /*
         * this next line is so that we talk to NCSA 1.5 which blatantly
         * breaks the http specifaction
         */
        if (!s) {
            s = strstr(c->cbuff, "\n\n");
            l = 2;
        }

        if (!s) {
            /* read rest next time */
            if (space) {
                return;
            }
            else {
            /* header is in invalid or too big - close connection */
                set_conn_state(c, STATE_UNCONNECTED);
                apr_socket_close(c->aprsock);
                err_response++;
                if (bad++ > 10) {
                    err("\nTest aborted after 10 failures\n\n");
                }
                start_connect(c);
            }
        }
        else {
            /* have full header */
            if (!good) {
                /*
                 * this is first time, extract some interesting info
                 */
                char *p, *q;
                size_t len = 0;
                p = xstrcasestr(c->cbuff, "Server:");
                q = servername;
                if (p) {
                    p += 8;
                    /* -1 to not overwrite last '\0' byte */
                    while (*p > 32 && len++ < sizeof(servername) - 1)
                        *q++ = *p++;
                }
                *q = 0;
            }
            /*
             * XXX: this parsing isn't even remotely HTTP compliant... but in
             * the interest of speed it doesn't totally have to be, it just
             * needs to be extended to handle whatever servers folks want to
             * test against. -djg
             */

            /* check response code */
            part = strstr(c->cbuff, "HTTP");    /* really HTTP/1.x_ */
            if (part && strlen(part) > strlen("HTTP/1.x_")) {
                strncpy(respcode, (part + strlen("HTTP/1.x_")), 3);
                respcode[3] = '\0';
            }
            else {
                strcpy(respcode, "500");
            }

            if (respcode[0] != '2') {
                err_response++;
                if (verbosity >= 2)
                    printf("WARNING: Response code not 2xx (%s)\n", respcode);
            }
            else if (verbosity >= 3) {
                printf("LOG: Response code = %s\n", respcode);
            }

            c->gotheader = 1;
            *s = 0;     /* terminate at end of header */
#ifdef _WAF_BENCH_ // don't check whether there's "Keep-Alive" in response header
            if (g_keepalive_for_real_traffic || (keepalive && xstrcasestr(c->cbuff, "Keep-Alive"))) {
#else // original code goes here
            if (keepalive && xstrcasestr(c->cbuff, "Keep-Alive")) {
#endif //_WAF_BENCH_ // // make sure not exceeding stats size
                char *cl;
                c->keepalive = 1;
                cl = xstrcasestr(c->cbuff, "Content-Length:");
                if (cl && method != HEAD) {
                    /* response to HEAD doesn't have entity body */
                    c->length = atoi(cl + 16);
                }
                else {
                    c->length = 0;
                }
            }
            c->bread += c->cbx - (s + l - c->cbuff) + r - tocopy;
            totalbread += c->bread;

            /* We have received the header, so we know this destination socket
             * address is working, so initialize all remaining requests. */
            if (!requests_initialized) {
                for (i = 1; i < concurrency; i++) {
                    con[i].socknum = i;
                    start_connect(&con[i]);
                }
                requests_initialized = 1;
            }
        }
    }
    else {
        /* outside header, everything we have read is entity body */
        c->bread += r;
        totalbread += r;
    }
    if (r == sizeof(buffer) && c->bread < c->length) {
        /* read was full, try more immediately (nonblocking already) */
        goto read_more;
    }

    if (c->keepalive && (c->bread >= c->length)) {
        /* finished a keep-alive connection */
        good++;
        /* save out time */
        if (good == 1) {
            /* first time here */
            doclen = c->bread;
        }
        else if ((c->bread != doclen) && !nolength) {
            bad++;
            err_length++;
        }
        if (done < requests) {
#ifdef _WAF_BENCH_ // make sure not exceeding stats size
            struct data *s = &stats[(done++)%g_stats_window]; 
#else // original code goes here
            struct data *s = &stats[done++];
#endif //_WAF_BENCH_ // // make sure not exceeding stats size
            doneka++;
            c->done      = apr_time_now();
            s->starttime = c->start;
            s->ctime     = ap_max(0, c->connect - c->start);
            s->time      = ap_max(0, c->done - c->start);
            s->waittime  = ap_max(0, c->beginread - c->endwrite);
            if (heartbeatres && !(done % heartbeatres)) {
                fprintf(stderr, "Completed %d requests\n", done);
                fflush(stderr);
            }
        }
        c->keepalive = 0;
        c->length = 0;
        c->gotheader = 0;
        c->cbx = 0;
        c->read = c->bread = 0;
        /* zero connect time with keep-alive */
        c->start = c->connect = lasttime = apr_time_now();
        set_conn_state(c, STATE_CONNECTED);
        write_request(c);
    }
}

/* --------------------------------------------------------- */

/* run the tests */

static void test(void)
{
    apr_time_t stoptime;
    apr_int16_t rtnev;
    apr_status_t rv;
    int i;
    apr_status_t status;
    int snprintf_res = 0;
#ifdef NOT_ASCII
    apr_size_t inbytes_left, outbytes_left;
#endif

    if (isproxy) {
        connecthost = apr_pstrdup(cntxt, proxyhost);
        connectport = proxyport;
    }
    else {
        connecthost = apr_pstrdup(cntxt, hostname);
        connectport = port;
    }

    if (!use_html) {
        printf("Benchmarking %s ", hostname);
    if (isproxy)
        printf("[through %s:%d] ", proxyhost, proxyport);
    printf("(be patient)%s",
           (heartbeatres ? "\n" : "..."));
#ifdef _WAF_BENCH_  // add "\n" even if heartbeat is 0
    if (!heartbeatres) printf("\n");
#endif // _WAF_BENCH_  // add "\n" even if heartbeat is 0
    fflush(stdout);
    }

    con = xcalloc(concurrency, sizeof(struct connection));

    /*
     * XXX: a way to calculate the stats without requiring O(requests) memory
     * XXX: would be nice.
     */
#ifdef _WAF_BENCH_  // fixed stats window, <= g_stats_window
    stats = xcalloc(ap_min(requests, g_stats_window), sizeof(struct data));
#else // orginal code goes here
    stats = xcalloc(requests, sizeof(struct data));
#endif // _WAF_BENCH_  , fixed stats window, <= g_stats_window

    if ((status = apr_pollset_create(&readbits, concurrency, cntxt,
                                     APR_POLLSET_NOCOPY)) != APR_SUCCESS) {
        apr_err("apr_pollset_create failed", status);
    }

    /* add default headers if necessary */
    if (!opt_host) {
        /* Host: header not overridden, add default value to hdrs */
        
#ifdef _WAF_BENCH_  // Host:localhost option, "-1"
        // if no HOST specified in arguments and g_add_localhost is not disabled (-1)
        // use "localhost" instead of host_field which comes from URL
        if (g_add_localhost) {
            host_field = "Localhost"; 
            colonhost = "";
        }
#endif //_WAF_BENCH_  , Host:localhost option, "-1"

        hdrs = apr_pstrcat(cntxt, hdrs, "Host: ", host_field, colonhost, "\r\n", NULL);
    }
    else {
        /* Header overridden, no need to add, as it is already in hdrs */
    }

#ifdef HAVE_TLSEXT
    if (is_ssl && tls_use_sni) {
        apr_ipsubnet_t *ip;
        if (((tls_sni = opt_host) || (tls_sni = hostname)) &&
            (!*tls_sni || apr_ipsubnet_create(&ip, tls_sni, NULL,
                                               cntxt) == APR_SUCCESS)) {
            /* IP not allowed in TLS SNI extension */
            tls_sni = NULL;
        }
    }
#endif

#ifdef _WAF_BENCH_ //  connection:close option, "-2"
    // if no Connection specified in arguments and g_add_connection_close is not disabled (-2)
    // Add "Connection:Close" in header
    if (g_add_connection_close && !opt_connection) {
        /* User-Agent: header not overridden, add default value to hdrs */
        hdrs = apr_pstrcat(cntxt, hdrs, "Connection: ", "Close", "\r\n", NULL);
    }
#endif // _WAF_BENCH_ , connection:close option, "-2"

    if (!opt_useragent) {
        /* User-Agent: header not overridden, add default value to hdrs */
        hdrs = apr_pstrcat(cntxt, hdrs, "User-Agent: ApacheBench/", AP_AB_BASEREVISION, "\r\n", NULL);
    }
    else {
        /* Header overridden, no need to add, as it is already in hdrs */
    }

    if (!opt_accept) {
        /* Accept: header not overridden, add default value to hdrs */
        hdrs = apr_pstrcat(cntxt, hdrs, "Accept: */*\r\n", NULL);
    }
    else {
        /* Header overridden, no need to add, as it is already in hdrs */
    }

    /* setup request */
    if (!send_body) {
        snprintf_res = apr_snprintf(request, sizeof(_request),
            "%s %s HTTP/1.0\r\n"
            "%s" "%s" "%s"
            "%s" "\r\n",
            method_str[method],
            (isproxy) ? fullurl : path,
            keepalive ? "Connection: Keep-Alive\r\n" : "",
            cookie, auth, hdrs);
    }
    else {
        snprintf_res = apr_snprintf(request,  sizeof(_request),
            "%s %s HTTP/1.0\r\n"
            "%s" "%s" "%s"
            "Content-length: %" APR_SIZE_T_FMT "\r\n"
            "Content-type: %s\r\n"
            "%s"
            "\r\n",
            method_str[method],
            (isproxy) ? fullurl : path,
            keepalive ? "Connection: Keep-Alive\r\n" : "",
            cookie, auth,
            postlen,
            (content_type != NULL) ? content_type : "text/plain", hdrs);
    }
    if (snprintf_res >= sizeof(_request)) {
        err("Request too long\n");
    }

    if (verbosity >= 2)
        printf("INFO: %s header == \n---\n%s\n---\n",
               method_str[method], request);

    reqlen = strlen(request);

    /*
     * Combine headers and (optional) post file into one continuous buffer
     */

#ifdef _WAF_BENCH_ // avoid copying post data to request
// previous system allocates one single buffer holding header and body
// wb uses seperate buffers to hold them, and send them seperately
    if (g_pkt_length > 0)
        fprintf(stderr, "\n read %zu packets from file with total length(%zu).\n", 
            g_MAX_PKT_COUNT, g_pkt_length);
#else // original code goes here
    if (send_body) {
        char *buff = xmalloc(postlen + reqlen + 1);
        strcpy(buff, request);
        memcpy(buff + reqlen, postdata, postlen);
        request = buff;
    }
#endif // _WAF_BENCH_ // avoid copying post data to request

#ifdef NOT_ASCII
    inbytes_left = outbytes_left = reqlen;
    status = apr_xlate_conv_buffer(to_ascii, request, &inbytes_left,
                   request, &outbytes_left);
    if (status || inbytes_left || outbytes_left) {
        fprintf(stderr, "only simple translation is supported (%d/%"
                        APR_SIZE_T_FMT "/%" APR_SIZE_T_FMT ")\n",
                        status, inbytes_left, outbytes_left);
        exit(1);
    }
#endif              /* NOT_ASCII */

    if (myhost) {
        /* This only needs to be done once */
        if ((rv = apr_sockaddr_info_get(&mysa, myhost, APR_UNSPEC, 0, 0, cntxt)) != APR_SUCCESS) {
            char buf[120];
            apr_snprintf(buf, sizeof(buf),
                         "apr_sockaddr_info_get() for %s", myhost);
            apr_err(buf, rv);
        }
    }

    /* This too */
    if ((rv = apr_sockaddr_info_get(&destsa, connecthost,
                                    myhost ? mysa->family : APR_UNSPEC,
                                    connectport, 0, cntxt))
       != APR_SUCCESS) {
        char buf[120];
        apr_snprintf(buf, sizeof(buf),
                 "apr_sockaddr_info_get() for %s", connecthost);
        apr_err(buf, rv);
    }

    /* ok - lets start */
    start = lasttime = apr_time_now();
    stoptime = tlimit ? (start + apr_time_from_sec(tlimit)) : AB_MAX;

#ifdef SIGINT
    /* Output the results if the user terminates the run early. */
    apr_signal(SIGINT, output_results);
#endif

    /* initialise first connection to determine destination socket address
     * which should be used for next connections. */
    con[0].socknum = 0;
    start_connect(&con[0]);

    do {
        apr_int32_t n;
        const apr_pollfd_t *pollresults, *pollfd;

        n = concurrency;
        do {
            status = apr_pollset_poll(readbits, aprtimeout, &n, &pollresults);
#ifdef _WAF_BENCH_ // print out the progress
            print_progress(0); 
#endif // _WAF_BENCH_, // print out the progress
        } while (APR_STATUS_IS_EINTR(status));
#ifdef _WAF_BENCH_ // wb will not quit when there's a timeout
       if (status == APR_TIMEUP) {
            struct connection *c = &con[0];
            if  (c->state != STATE_READ) 
                apr_err("Timeout_in_non_STATE_READ", status);
            else {              
                err_recv++;
                bad ++;
                if (recverrok) {
                    if (verbosity > 1)
                        fprintf(stderr, "WARNING: READ TIMEOUT!\n");
                    save_logfile("TIMEOUT: READ ERROR\n",0);
                    close_connection(c);
                    continue;
                } else {
                    apr_err("Read_Timeout", status);
                }
            }
        } else 
#endif // _WAF_BENCH_, // wb will not quit when there's a timeout
        if (status != APR_SUCCESS)
            apr_err("apr_pollset_poll", status);

        for (i = 0, pollfd = pollresults; i < n; i++, pollfd++) {
            struct connection *c;

            c = pollfd->client_data;

            /*
             * If the connection isn't connected how can we check it?
             */
            if (c->state == STATE_UNCONNECTED)
                continue;

            rtnev = pollfd->rtnevents;

#ifdef USE_SSL
            if (c->state == STATE_CONNECTED && c->ssl && SSL_in_init(c->ssl)) {
                ssl_proceed_handshake(c);
                continue;
            }
#endif

            /*
             * Notes: APR_POLLHUP is set after FIN is received on some
             * systems, so treat that like APR_POLLIN so that we try to read
             * again.
             *
             * Some systems return APR_POLLERR with APR_POLLHUP.  We need to
             * call read_connection() for APR_POLLHUP, so check for
             * APR_POLLHUP first so that a closed connection isn't treated
             * like an I/O error.  If it is, we never figure out that the
             * connection is done and we loop here endlessly calling
             * apr_poll().
             */
            if ((rtnev & APR_POLLIN) || (rtnev & APR_POLLPRI) || (rtnev & APR_POLLHUP))
                read_connection(c);
            if ((rtnev & APR_POLLERR) || (rtnev & APR_POLLNVAL)) {
                if (destsa->next && c->state == STATE_CONNECTING && good == 0) {
                    destsa = destsa->next;
                    start_connect(c);
                }
                else {
                    bad++;
                    err_except++;
                    /* avoid apr_poll/EINPROGRESS loop on HP-UX, let recv discover ECONNREFUSED */
                    if (c->state == STATE_CONNECTING) {
                        read_connection(c);
                    }
                    else {
                        start_connect(c);
                    }
                }
                continue;
            }
            if (rtnev & APR_POLLOUT) {
                if (c->state == STATE_CONNECTING) {
                    /* call connect() again to detect errors */
                    rv = apr_socket_connect(c->aprsock, destsa);
                    if (rv != APR_SUCCESS) {
                        set_conn_state(c, STATE_UNCONNECTED);
                        apr_socket_close(c->aprsock);
                        err_conn++;
                        if (bad++ > 10) {
                            fprintf(stderr,
                                    "\nTest aborted after 10 failures\n\n");
                            apr_err("apr_socket_connect()", rv);
                        }
                        start_connect(c);
                        continue;
                    }
                    else {
                        set_conn_state(c, STATE_CONNECTED);
#ifdef USE_SSL
                        if (c->ssl)
                            ssl_proceed_handshake(c);
                        else
#endif
                        write_request(c);
                    }
                }
                else {
                    /* POLLOUT is one shot */
                    set_polled_events(c, APR_POLLIN);
                    if (c->state == STATE_READ) {
                        read_connection(c);
                    }
                    else {
                        write_request(c);
                    }
                }
            }
        }
    } while (lasttime < stoptime && done < requests);

#ifdef _WAF_BENCH_ // print out the last progress
    if (g_interval_print) {
        print_progress(1); // forced print out
        fprintf(stderr, "Finished %d requests", done);
    } else 
#endif // _WAF_BENCH_, // print out the last progress
    if (heartbeatres)
        fprintf(stderr, "Finished %d requests\n", done);
    else
        printf("..done\n");

    if (use_html)
        output_html_results();
    else
        output_results(0);
}

/* ------------------------------------------------------- */

/* display copyright information */
static void copyright(void)
{
    if (!use_html) {
#ifdef _WAF_BENCH_ // print waf-bench version
        fprintf(stderr,"\033[0m"); // no color
        printf("WAF-Bench(wb) Version "WAF_BENCH_VERSION"(Build: "__DATE__ " " __TIME__").\n");
		printf("  By Networking Research Group of Microsoft Research, 2018.\n");
        printf("wb is based on ApacheBench, Version %s\n", AP_AB_BASEREVISION " <1818629>");
        printf("\n");
        return;
#endif //_WAF_BENCH_ // print waf-bench version
        printf("This is ApacheBench, Version %s\n", AP_AB_BASEREVISION " <$Revision$>");
        printf("Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/\n");
        printf("Licensed to The Apache Software Foundation, http://www.apache.org/\n");
        printf("\n");
    }
    else {
        printf("<p>\n");
#ifdef _WAF_BENCH_ // print waf-bench version
        printf("WAF-Bench(wb) Version "WAF_BENCH_VERSION"(Build: "__DATE__ " " __TIME__").<br>\n");
		printf("  By Networking Research Group of Microsoft Research, 2018.<br>\n");
        printf("wb is based on ApacheBench, Version %s <i>&lt;%s&gt;</i><br>\n", AP_AB_BASEREVISION, "1818629");
        printf("</p>\n<p>\n");
        return;
#endif //_WAF_BENCH_ // print waf-bench version
        printf(" This is ApacheBench, Version %s <i>&lt;%s&gt;</i><br>\n", AP_AB_BASEREVISION, "$Revision$");
        printf(" Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/<br>\n");
        printf(" Licensed to The Apache Software Foundation, http://www.apache.org/<br>\n");
        printf("</p>\n<p>\n");
    }
}

/* display usage information */
static void usage(const char *progname)
{
#ifdef _WAF_BENCH_  // print waf-bench version
    copyright();
#endif //_WAF_BENCH_ // print waf-bench version

    fprintf(stderr, "Usage: %s [options] [http"
#ifdef USE_SSL
        "[s]"
#endif
        "://]hostname[:port]/path\n", progname);
/* 80 column ruler:  ********************************************************************************
 */
    fprintf(stderr, "Options are:\n");
    fprintf(stderr, "    -n requests     Number of requests to perform\n");
    fprintf(stderr, "    -c concurrency  Number of multiple requests to make at a time\n");
    fprintf(stderr, "    -t timelimit    Seconds to max. to spend on benchmarking\n");
#ifdef _WAF_BENCH_ // remove 50000 limits when specifying "-t"
    fprintf(stderr, "       default: %d, namely test %d seconds if \"-n\" is not specified.\n",
                            DEFAULT_TEST_TIME,DEFAULT_TEST_TIME );
// we don't need the following 50,000 limitation implication
#else
    fprintf(stderr, "                    This implies -n 50000\n");
#endif //_WAF_BENCH_  // remove 50000 limits when specifying "-t"
    fprintf(stderr, "    -s timeout      Seconds to max. wait for each response\n");
    fprintf(stderr, "                    Default is 30 seconds\n");
    fprintf(stderr, "    -b windowsize   Size of TCP send/receive buffer, in bytes\n");
    fprintf(stderr, "    -B address      Address to bind to when making outgoing connections\n");
    fprintf(stderr, "    -p postfile     File containing data to POST. Remember also to set -T\n");
    fprintf(stderr, "    -u putfile      File containing data to PUT. Remember also to set -T\n");
    fprintf(stderr, "    -T content-type Content-type header to use for POST/PUT data, eg.\n");
    fprintf(stderr, "                    'application/x-www-form-urlencoded'\n");
    fprintf(stderr, "                    Default is 'text/plain'\n");
    fprintf(stderr, "    -v verbosity    How much troubleshooting info to print\n");
    fprintf(stderr, "    -w              Print out results in HTML tables\n");
    fprintf(stderr, "    -i              Use HEAD instead of GET\n");
    fprintf(stderr, "    -x attributes   String to insert as table attributes\n");
    fprintf(stderr, "    -y attributes   String to insert as tr attributes\n");
    fprintf(stderr, "    -z attributes   String to insert as td or th attributes\n");
    fprintf(stderr, "    -C attribute    Add cookie, eg. 'Apache=1234'. (repeatable)\n");
    fprintf(stderr, "    -H attribute    Add Arbitrary header line, eg. 'Accept-Encoding: gzip'\n");
    fprintf(stderr, "                    Inserted after all normal header lines. (repeatable)\n");
    fprintf(stderr, "    -A attribute    Add Basic WWW Authentication, the attributes\n");
    fprintf(stderr, "                    are a colon separated username and password.\n");
    fprintf(stderr, "    -P attribute    Add Basic Proxy Authentication, the attributes\n");
    fprintf(stderr, "                    are a colon separated username and password.\n");
    fprintf(stderr, "    -X proxy:port   Proxyserver and port number to use\n");
    fprintf(stderr, "    -V              Print version number and exit\n");
    fprintf(stderr, "    -k              Use HTTP KeepAlive feature\n");
    fprintf(stderr, "    -d              Do not show percentiles served table.\n");
    fprintf(stderr, "    -S              Do not show confidence estimators and warnings.\n");
    fprintf(stderr, "    -q              Do not show progress when doing more than 150 requests\n");
    fprintf(stderr, "    -l              Accept variable document length (use this for dynamic pages)\n");
    fprintf(stderr, "    -g filename     Output collected data to gnuplot format file.\n");
    fprintf(stderr, "    -e filename     Output CSV file with percentages served\n");
    fprintf(stderr, "    -r              Don't exit on socket receive errors.\n");
    fprintf(stderr, "    -m method       Method name\n");
    fprintf(stderr, "    -h              Display usage information (this message)\n");
#ifdef USE_SSL

#ifndef OPENSSL_NO_SSL2
#define SSL2_HELP_MSG "SSL2, "
#else
#define SSL2_HELP_MSG ""
#endif

#ifndef OPENSSL_NO_SSL3
#define SSL3_HELP_MSG "SSL3, "
#else
#define SSL3_HELP_MSG ""
#endif

#ifdef HAVE_TLSV1_X
#define TLS1_X_HELP_MSG ", TLS1.1, TLS1.2"
#else
#define TLS1_X_HELP_MSG ""
#endif

#ifdef HAVE_TLSEXT
    fprintf(stderr, "    -I              Disable TLS Server Name Indication (SNI) extension\n");
#endif
    fprintf(stderr, "    -Z ciphersuite  Specify SSL/TLS cipher suite (See openssl ciphers)\n");
    fprintf(stderr, "    -f protocol     Specify SSL/TLS protocol\n");
    fprintf(stderr, "                    (" SSL2_HELP_MSG SSL3_HELP_MSG "TLS1" TLS1_X_HELP_MSG " or ALL)\n");
#endif

#ifdef _WAF_BENCH_ // print waf-bench new usage
    fprintf(stderr,"\033[1;33m\n"); // Yellow
    fprintf(stderr, "New options for wb:\n");
    fprintf(stderr,"\033[0m\n"); // no color
    fprintf(stderr, "    -F pkt_file     File of packet seperated by \\0 or a leading size\n");
    fprintf(stderr, "                    note: \"-n\" now is the total times to be sent for pkt_file\n");
    fprintf(stderr, "    -G max_size     Maximum output file size (in MB, default=0:unlimited)\n");
    fprintf(stderr, "    -j interval     Progress report interval (set 0 to disable, default=1)\n");
    fprintf(stderr, "    -J sub_string   Replace the sub_string in pkt content with <seq#> of wb\n");
    fprintf(stderr, "    -K              Keep body during save (default: save header only)\n");
    fprintf(stderr, "    -o msg_file     Save received http messages to filename\n");
    fprintf(stderr, "    -Q max_count    # of packets in packet file (default=0:all pkts in file)\n");
    fprintf(stderr, "    -U URL_prefix   Add prefix \"/URL_prefix<seq#>/\" to each request URL\n");
    fprintf(stderr, "    -W stats_num    Window of stats, number of stats values (default=50000)\n");
    fprintf(stderr, "    -1              (for testing) Don't append Host:localhost if absent (\n");
    fprintf(stderr, "                    default to add)\n");
    fprintf(stderr, "    -2 option       (for testing)  Don't append Connection:close if option is 0, \n");
    fprintf(stderr, "                    Append connection:close to those packets without connection attribution if option is 1,\n");
    fprintf(stderr, "                    Append or replace connection attribution to close for any packets if option is 2\n");
    fprintf(stderr, "    -3              (for testing) Use micro-second granularity in output,\n");
    fprintf(stderr, "                    default disabled\n");
/*
    fprintf(stderr, "    -D min_time     Lower bound of stats histogram(us) (default: 0 us)\n");
    fprintf(stderr, "    -U max_time     Upper bound of stats histogram(us) (default: 10000 us)\n");
    fprintf(stderr, "    -N              (TBD) Number of threads\n");
    fprintf(stderr, "    -3-9            (TBD)\n");
*/
#endif //_WAF_BENCH_ // print waf-bench new usage

    exit(EINVAL);
}

/* ------------------------------------------------------- */

/* split URL into parts */

static int parse_url(const char *url)
{
    char *cp;
    char *h;
    char *scope_id;
    apr_status_t rv;

    /* Save a copy for the proxy */
    fullurl = apr_pstrdup(cntxt, url);

    if (strlen(url) > 7 && strncmp(url, "http://", 7) == 0) {
        url += 7;
#ifdef USE_SSL
        is_ssl = 0;
#endif
    }
    else
#ifdef USE_SSL
    if (strlen(url) > 8 && strncmp(url, "https://", 8) == 0) {
        url += 8;
        is_ssl = 1;
    }
#else
    if (strlen(url) > 8 && strncmp(url, "https://", 8) == 0) {
        fprintf(stderr, "SSL not compiled in; no https support\n");
        exit(1);
    }
#endif

    if ((cp = strchr(url, '/')) == NULL)
#ifdef _WAF_BENCH_ // we can omit the '/' if it's the end
        // no '/' is found, put cp to the end
        cp = (char *)url + strlen(url);
#else
        return 1;
#endif //_WAF_BENCH_ , we can omit the '/' if it's the end
    h = apr_pstrmemdup(cntxt, url, cp - url);
    rv = apr_parse_addr_port(&hostname, &scope_id, &port, h, cntxt);
    if (rv != APR_SUCCESS || !hostname || scope_id) {
        return 1;
    }
    path = apr_pstrdup(cntxt, cp);
#ifdef _WAF_BENCH_ // we can omit the '/' if it's the end
    if (*cp == '\0') // append "/" to path
        path = apr_pstrdup(cntxt, "/");
#endif //_WAF_BENCH_ , we can omit the '/' if it's the end

    *cp = '\0';
    if (*url == '[') {      /* IPv6 numeric address string */
        host_field = apr_psprintf(cntxt, "[%s]", hostname);
    }
    else {
        host_field = hostname;
    }

    if (port == 0) {        /* no port specified */
#ifdef USE_SSL
        if (is_ssl)
            port = 443;
        else
#endif
        port = 80;
    }

    if ((
#ifdef USE_SSL
         is_ssl && (port != 443)) || (!is_ssl &&
#endif
         (port != 80)))
    {
        colonhost = apr_psprintf(cntxt,":%d",port);
    } else
        colonhost = "";
    return 0;
}

/* ------------------------------------------------------- */

/* read data to POST/PUT from file, save contents and length */

static apr_status_t open_postfile(const char *pfile)
{
    apr_file_t *postfd;
    apr_finfo_t finfo;
    apr_status_t rv;
    char errmsg[120];

    rv = apr_file_open(&postfd, pfile, APR_READ, APR_OS_DEFAULT, cntxt);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "ab: Could not open POST data file (%s): %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }

    rv = apr_file_info_get(&finfo, APR_FINFO_NORM, postfd);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "ab: Could not stat POST data file (%s): %s\n", pfile,
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }
    postlen = (apr_size_t)finfo.size;
    postdata = xmalloc(postlen);
    rv = apr_file_read_full(postfd, postdata, postlen, NULL);
    if (rv != APR_SUCCESS) {
        fprintf(stderr, "ab: Could not read POST data file: %s\n",
                apr_strerror(rv, errmsg, sizeof errmsg));
        return rv;
    }
    apr_file_close(postfd);
    return APR_SUCCESS;
}

/* ------------------------------------------------------- */

/* sort out command-line args and call test */
int main(int argc, const char * const argv[])
{
    int l;
    char tmp[1024];
    apr_status_t status;
    apr_getopt_t *opt;
    const char *opt_arg;
    char c;
#if OPENSSL_VERSION_NUMBER >= 0x10100000L
    int max_prot = TLS1_2_VERSION;
#ifndef OPENSSL_NO_SSL3
    int min_prot = SSL3_VERSION;
#else
    int min_prot = TLS1_VERSION;
#endif
#endif /* #if OPENSSL_VERSION_NUMBER >= 0x10100000L */
#ifdef USE_SSL
    AB_SSL_METHOD_CONST SSL_METHOD *meth = SSLv23_client_method();
#endif

    /* table defaults  */
    tablestring = "";
    trstring = "";
    tdstring = "bgcolor=white";
    cookie = "";
    auth = "";
    proxyhost = "";
    hdrs = "";

    setbuf(stdout, NULL);
    apr_app_initialize(&argc, &argv, NULL);
    atexit(apr_terminate);
    apr_pool_create(&cntxt, NULL);
    apr_pool_abort_set(abort_on_oom, cntxt);

#ifdef NOT_ASCII
    status = apr_xlate_open(&to_ascii, "ISO-8859-1", APR_DEFAULT_CHARSET, cntxt);
    if (status) {
        fprintf(stderr, "apr_xlate_open(to ASCII)->%d\n", status);
        exit(1);
    }
    status = apr_xlate_open(&from_ascii, APR_DEFAULT_CHARSET, "ISO-8859-1", cntxt);
    if (status) {
        fprintf(stderr, "apr_xlate_open(from ASCII)->%d\n", status);
        exit(1);
    }
    status = apr_base64init_ebcdic(to_ascii, from_ascii);
    if (status) {
        fprintf(stderr, "apr_base64init_ebcdic()->%d\n", status);
        exit(1);
    }
#endif

#ifdef _WAF_BENCH_ // loop for parse args
    g_new_header = xmalloc(g_header_len_MAX);
    g_sub_string = (char **)xcalloc(g_sub_string_num_MAX, sizeof(char *));
    if (argv[0][strlen(argv[0]) - 1] == '0')
        g_enable_ini = 1; // if progname = "wb0" then enable ini

    fprintf(stderr,"\033[1;33m"); // Yellow
    // parsed_args_rounds indicates the current round of parsing args
    int parsed_args_rounds = 0;
PARSE_ARGS:
    // 1:First CLI, 2:INI+CLI, no more than 3 rounds
    parsed_args_rounds ++;
#endif // _WAF_BENCH_ loop for parse args
    myhost = NULL; /* 0.0.0.0 or :: */

    apr_getopt_init(&opt, cntxt, argc, argv);
    while ((status = apr_getopt(opt, "n:c:t:s:b:T:p:u:v:lrkVhwiIx:y:z:C:H:P:A:g:X:de:SqB:m:"
#ifdef USE_SSL
            "Z:f:"
#endif
#ifdef _WAF_BENCH_ // adding more options 0-9,aFINRDUYWEGKQ 
            "Y:a:o:F:j:J:O:R:D:U:Y:W:E:G:Q:K012:3456789"
#endif // _WAF_BENCH_, adding more options 0-9,aFINRDUYWEGKQ 
            ,&c, &opt_arg)) == APR_SUCCESS) {
        switch (c) {
#ifdef _WAF_BENCH_ // more new features of waf-bench
            case '0': // enable read/write ini file for wb's options
                g_enable_ini = 1;
                break;
            case '1': // Don't append Host:localhost if it is set
                g_add_localhost = 0;
                break;
            case '2': // Don't append Connection:close if option is 0, 
                      // Append connection:close to those packets without connection attribution if option is 1,
                      // Append or replace connection attribution to close for any packets if option is 2
                g_add_connection_close = atoi(opt_arg);
                if (g_add_connection_close < 0 || g_add_connection_close > 2) {
                    err("Error option to -2\n");
                }
                break;
            case '3': // microsec-granularity in output-results
                // by default, it's not microsec-granularity
                // but you can change the default value and use -3 to toggle it
                g_us_granularity = !g_us_granularity; 
                break;
            case 'K': // save body or not?
                g_save_body = 1;
                break;
            case 'Q': // max number of packets in pkt file
                g_MAX_PKT_COUNT= atoi(opt_arg) ;
                if (g_MAX_PKT_COUNT < 0) 
                    err("Invalid max packet count\n");
                break;
            case 'R': // RPS number for rate limiting
                {
                int rps_scale = 1;
                if (opt_arg[strlen(opt_arg) - 1] == 'k' || opt_arg[strlen(opt_arg) - 1] == 'K')
                   rps_scale = 1000;
                else if (opt_arg[strlen(opt_arg) - 1] == 'm' || opt_arg[strlen(opt_arg) - 1] == 'M')
                   rps_scale = 1000000;
                else if (opt_arg[strlen(opt_arg) - 1] == 'g' || opt_arg[strlen(opt_arg) - 1] == 'G')
                   rps_scale = 1000000000;
                if (rps_scale == 1)                
                    g_RPS_NUMBER= atoi(opt_arg) ;
                else 
                    g_RPS_NUMBER= rps_scale * atof(opt_arg) ;
                if (g_MAX_PKT_COUNT < 0) 
                    err("Invalid number for RPS (Request per second)\n");
                }
                break;
            case 'G': // max log file size
                g_MAX_FILE_SIZE = atoi(opt_arg) * MB;
                if (g_MAX_FILE_SIZE < 0) 
                    err("Invalid max file size\n");
                break;
            case 'Y': 
            case 'U': // Add prefix("/prefix<seq#>/" to URL
                g_opt_prefix = xstrdup(opt_arg);
                break;
            case 'J': // subsistute sub_string with seq# inside header
                g_sub_string[g_sub_string_num++] = xstrdup(opt_arg);
                if (g_sub_string_num == g_sub_string_num_MAX) {
                    g_sub_string_num_MAX <<= 1;
                    char **sub_string_new;
                    sub_string_new = xcalloc(g_sub_string_num_MAX, sizeof (char *));
                    memcpy(sub_string_new,g_sub_string,g_sub_string_num*sizeof(char *));
                    free(g_sub_string);
                    g_sub_string = sub_string_new;
                }
                break;
            case 'o': // file to save received http messages
                g_save_filename = xstrdup(opt_arg);
                break;
            case 'a':
            case 'F': // a packet file to be sent
                g_pkt_filename = xstrdup(opt_arg);
                break;
            case 'E': // input ini file to be Executed
                opt_file_in = xstrdup(opt_arg);
                break;
            case 'O': // Output ini file to be saved
                opt_file_out = xstrdup(opt_arg);
                break;
            case 'j': // Interval (in secs) of progress report
                g_interval_print = atoi(opt_arg);
                if (g_interval_print < 0) 
                    err("Invalid print interval\n");
                break;
            case 'W': // stats size
                g_stats_window= atoi(opt_arg);
                if (g_stats_window <= 0) 
                    err("Invalid stats size\n");
                break;
            case '4': // keepalive_for_real_traffic
                g_keepalive_for_real_traffic  = 1;
                break;
            case '5': // print out additional progress info
                g_extended_progress = 1;
                break;
#endif // _WAF_BENCH_ end of new arguments processing

            case 'n':
                requests = atoi(opt_arg);
                if (requests <= 0) {
                    err("Invalid number of requests\n");
                }
#ifdef _WAF_BENCH_ // request is specified
                g_set_requests = 1;
#endif //_WAF_BENCH_, request is specified
                break;
            case 'k':
                keepalive = 1;
				g_add_connection_close  = 0;
                break;
            case 'q':
                heartbeatres = 0;
                break;
            case 'c':
                concurrency = atoi(opt_arg);
                break;
            case 'b':
                windowsize = atoi(opt_arg);
                break;
            case 'i':
                if (method != NO_METH)
                    err("Cannot mix HEAD with other methods\n");
                method = HEAD;
                break;
            case 'g':
                gnuplot = xstrdup(opt_arg);
                break;
            case 'd':
                percentile = 0;
                break;
            case 'e':
                csvperc = xstrdup(opt_arg);
                break;
            case 'S':
                confidence = 0;
                break;
            case 's':
                aprtimeout = apr_time_from_sec(atoi(opt_arg)); /* timeout value */
                break;
            case 'p':
                if (method != NO_METH)
                    err("Cannot mix POST with other methods\n");
#ifdef _WAF_BENCH_ // open those file after parsing all arguments
                g_post_filename = xstrdup(opt_arg); 
#else // original code goes here
                if (open_postfile(opt_arg) != APR_SUCCESS) {
                    exit(1);
                }
#endif //_WAF_BENCH_ // open post file after parsing all arguments
                
                method = POST;
                send_body = 1;
                break;
            case 'u':
                if (method != NO_METH)
                    err("Cannot mix PUT with other methods\n");
#ifdef _WAF_BENCH_ // open put file after parsing all arguments
                g_put_filename = xstrdup(opt_arg);  
#else // original code goes here
                if (open_postfile(opt_arg) != APR_SUCCESS) {
                    exit(1);
                }
#endif //_WAF_BENCH_ // open put file after parsing all arguments
                method = PUT;
                send_body = 1;
                break;
            case 'l':
                nolength = 1;
                break;
            case 'r':
                recverrok = 1;
                break;
            case 'v':
                verbosity = atoi(opt_arg);
                break;
            case 't':
                tlimit = atoi(opt_arg);
#ifdef _WAF_BENCH_ // set requests to max only when request is specified
                if (!g_set_requests)
#endif //_WAF_BENCH_, set requests to max only when request is specified
                requests = MAX_REQUESTS;    /* need to size data array on
                                             * something */
                break;
            case 'T':
                content_type = apr_pstrdup(cntxt, opt_arg);
                break;
            case 'C':
                cookie = apr_pstrcat(cntxt, "Cookie: ", opt_arg, "\r\n", NULL);
                break;
            case 'A':
                /*
                 * assume username passwd already to be in colon separated form.
                 * Ready to be uu-encoded.
                 */
                while (apr_isspace(*opt_arg))
                    opt_arg++;
                if (apr_base64_encode_len(strlen(opt_arg)) > sizeof(tmp)) {
                    err("Authentication credentials too long\n");
                }
                l = apr_base64_encode(tmp, opt_arg, strlen(opt_arg));
                tmp[l] = '\0';

                auth = apr_pstrcat(cntxt, auth, "Authorization: Basic ", tmp,
                                       "\r\n", NULL);
                break;
            case 'P':
                /*
                 * assume username passwd already to be in colon separated form.
                 */
                while (apr_isspace(*opt_arg))
                opt_arg++;
                if (apr_base64_encode_len(strlen(opt_arg)) > sizeof(tmp)) {
                    err("Proxy credentials too long\n");
                }
                l = apr_base64_encode(tmp, opt_arg, strlen(opt_arg));
                tmp[l] = '\0';

                auth = apr_pstrcat(cntxt, auth, "Proxy-Authorization: Basic ",
                                       tmp, "\r\n", NULL);
                break;
            case 'H':
                hdrs = apr_pstrcat(cntxt, hdrs, opt_arg, "\r\n", NULL);
                /*
                 * allow override of some of the common headers that ab adds
                 */
                if (strncasecmp(opt_arg, "Host:", 5) == 0) {
                    char *host;
                    apr_size_t len;
                    opt_arg += 5;
                    while (apr_isspace(*opt_arg))
                        opt_arg++;
                    len = strlen(opt_arg);
                    host = strdup(opt_arg);
                    while (len && apr_isspace(host[len-1]))
                        host[--len] = '\0';
                    opt_host = host;
                } else if (strncasecmp(opt_arg, "Accept:", 7) == 0) {
                    opt_accept = 1;
                    
#ifdef _WAF_BENCH_ // Connection:close header
                } else if (strncasecmp(opt_arg, "Connection:", 11) == 0) {
                    opt_connection = 1;
#endif // _WAF_BENCH_ // Connection:close header                
                } else if (strncasecmp(opt_arg, "User-Agent:", 11) == 0) {
                    opt_useragent = 1;
                }
                break;
            case 'w':
                use_html = 1;
                break;
                /*
                 * if any of the following three are used, turn on html output
                 * automatically
                 */
            case 'x':
                use_html = 1;
                tablestring = opt_arg;
                break;
            case 'X':
                {
                    char *p;
                    /*
                     * assume proxy-name[:port]
                     */
                    if ((p = strchr(opt_arg, ':'))) {
                        *p = '\0';
                        p++;
                        proxyport = atoi(p);
                    }
                    proxyhost = apr_pstrdup(cntxt, opt_arg);
                    isproxy = 1;
                }
                break;
            case 'y':
                use_html = 1;
                trstring = opt_arg;
                break;
            case 'z':
                use_html = 1;
                tdstring = opt_arg;
                break;
            case 'h':
                usage(argv[0]);
                break;
            case 'V':
                copyright();
                return 0;
            case 'B':
                myhost = apr_pstrdup(cntxt, opt_arg);
                break;
            case 'm':
                method = CUSTOM_METHOD;
                method_str[CUSTOM_METHOD] = strdup(opt_arg);
                break;
#ifdef USE_SSL
            case 'Z':
                ssl_cipher = strdup(opt_arg);
                break;
            case 'f':
#if OPENSSL_VERSION_NUMBER < 0x10100000L
                if (strncasecmp(opt_arg, "ALL", 3) == 0) {
                    meth = SSLv23_client_method();
#ifndef OPENSSL_NO_SSL2
                } else if (strncasecmp(opt_arg, "SSL2", 4) == 0) {
                    meth = SSLv2_client_method();
#ifdef HAVE_TLSEXT
                    tls_use_sni = 0;
#endif
#endif
#ifndef OPENSSL_NO_SSL3
                } else if (strncasecmp(opt_arg, "SSL3", 4) == 0) {
                    meth = SSLv3_client_method();
#ifdef HAVE_TLSEXT
                    tls_use_sni = 0;
#endif
#endif
#ifdef HAVE_TLSV1_X
                } else if (strncasecmp(opt_arg, "TLS1.1", 6) == 0) {
                    meth = TLSv1_1_client_method();
                } else if (strncasecmp(opt_arg, "TLS1.2", 6) == 0) {
                    meth = TLSv1_2_client_method();
#endif
                } else if (strncasecmp(opt_arg, "TLS1", 4) == 0) {
                    meth = TLSv1_client_method();
                }
#else /* #if OPENSSL_VERSION_NUMBER < 0x10100000L */
                meth = TLS_client_method();
                if (strncasecmp(opt_arg, "ALL", 3) == 0) {
                    max_prot = TLS1_2_VERSION;
#ifndef OPENSSL_NO_SSL3
                    min_prot = SSL3_VERSION;
#else
                    min_prot = TLS1_VERSION;
#endif
#ifndef OPENSSL_NO_SSL3
                } else if (strncasecmp(opt_arg, "SSL3", 4) == 0) {
                    max_prot = SSL3_VERSION;
                    min_prot = SSL3_VERSION;
#endif
                } else if (strncasecmp(opt_arg, "TLS1.1", 6) == 0) {
                    max_prot = TLS1_1_VERSION;
                    min_prot = TLS1_1_VERSION;
                } else if (strncasecmp(opt_arg, "TLS1.2", 6) == 0) {
                    max_prot = TLS1_2_VERSION;
                    min_prot = TLS1_2_VERSION;
                } else if (strncasecmp(opt_arg, "TLS1", 4) == 0) {
                    max_prot = TLS1_VERSION;
                    min_prot = TLS1_VERSION;
                }
#endif /* #if OPENSSL_VERSION_NUMBER < 0x10100000L */
                break;
#ifdef HAVE_TLSEXT
            case 'I':
                tls_use_sni = 0;
                break;
#endif
#endif
        }
    }

#ifdef _WAF_BENCH_ // open those files after parsing all arguments
    // enable ini if ini_file_in/out are set
    if ((g_enable_ini || opt_file_in) && parsed_args_rounds == 1) { 
        // read wb.ini, if ini file is valid, go back to parse ini
        // otherwise, go directly to process args
        opt_string = (char *)xmalloc(g_opt_string_len);
        g_argv_ini = (char **)xcalloc(g_opt_string_len, sizeof (char*));
        if (read_inifile(opt_file_in, opt_string) == APR_SUCCESS) {
            g_argc_ini = parse_opt_string(opt_string, g_argv_ini);
            if (g_argc_ini) { // parse the options again
                int i, j;
                int cli_url = 1;

                // append CLI options at the end of INI options
                if (opt->ind != argc - 1) { //CLI options don't have URL
                    cli_url = 0; 
                    // save the ini URL at the end of argv
                    g_argv_ini[argc+g_argc_ini-1] = g_argv_ini[g_argc_ini];
                }
                for (i = 1, j = g_argc_ini; i < argc; i ++, j ++)
                    g_argv_ini[j] = (char *)argv[i];
                    
                g_argv_ini[0] = (char *)argv[0]; // save the prog name
                argc += g_argc_ini - cli_url; 
                argv = (const char **)g_argv_ini;
                goto PARSE_ARGS;
            }
        }
    }
    
    // open those files after parsing all arguments
    if ((g_save_filename && open_file_for_write(g_save_filename, &g_save_file_fd) != APR_SUCCESS) // -R option 
        || (g_put_filename && open_postfile(g_put_filename) != APR_SUCCESS) // -u option 
        || (g_pkt_filename && open_pktfile(g_pkt_filename) != APR_SUCCESS) // -F option 
        || (g_post_filename && open_postfile(g_post_filename) != APR_SUCCESS)) // -p option
        exit(1);

    /*
     * if -n not specified, set requests to MAX
     * furthermore, if -t is not specified, set it to default
     * -n and -t might be specified at the same time
     * if -n is specified, we should not set -t to default
     * namely, -n 50000 != -n 50000 -t 10
     * because 50000 requests may take time > 10 seconds
     * so need to put "-t" processing logic inside "-n".
     */
    if (!g_set_requests) {
        requests = INT_MAX;
        if (tlimit == 0) {
            tlimit = DEFAULT_TEST_TIME;
        }
    } else {
        // we treat "-n" as the total times to be sent for the whole pkt file
        if (g_pkt_count)
            requests = requests * g_pkt_count;
    }

    // if we need save response to g_save_filename, only 1 connection can be used
    if (g_save_filename) {
        if (concurrency > 1) {
            fprintf(stderr, "WARNING: To save response to %s, only 1 connection can be used, so ignore -c %d!\n", 
                g_save_filename, concurrency);
            concurrency = 1;
        }
    }
    // disable previous req# based heartbeat, use time-based print interval
    heartbeatres = 0; 
    g_interval_print = g_interval_print * APR_USEC_PER_SEC; 

    // use milli-second as the timeout unit when finer granularity is chosen
    //if (g_us_granularity)
    //  aprtimeout = aprtimeout / 1000; // original value is "sec", now use "ms"
        
    if (verbosity >= 4) {
        printf("INFO: ARGS[%d] =", argc);
        int i = 0;
        for (i = 0; i < argc; i ++)
            printf(" %s",argv[i]);
        printf("\n");
    }
    // save the options to ini
    if (opt_file_out || g_enable_ini)
        write_inifile(opt_file_out, argc, (char **)argv);

	if (argc == 1) {
        usage(argv[0]);
    }
#endif // _WAF_BENCH_ // open those files after parsing all arguments

    if (opt->ind != argc - 1) {
        fprintf(stderr, "%s: wrong number of arguments\n", argv[0]);
        usage(argv[0]);
    }

    if (method == NO_METH) {
        method = GET;
    }

    if (parse_url(apr_pstrdup(cntxt, opt->argv[opt->ind++]))) {
        fprintf(stderr, "%s: invalid URL\n", argv[0]);
        usage(argv[0]);
    }

    if ((concurrency < 0) || (concurrency > MAX_CONCURRENCY)) {
        fprintf(stderr, "%s: Invalid Concurrency [Range 0..%d]\n",
                argv[0], MAX_CONCURRENCY);
        usage(argv[0]);
    }

#ifndef _WAF_BENCH_ // concurrency can be greater than requests
    if (concurrency > requests) {
        fprintf(stderr, "%s: Cannot use concurrency level greater than "
                "total number of requests\n", argv[0]);
        usage(argv[0]);
    }
#endif // _WAF_BENCH_ // concurrency can be greater than requests

    if ((heartbeatres) && (requests > 150)) {
        heartbeatres = requests / 10;   /* Print line every 10% of requests */
        if (heartbeatres < 100)
            heartbeatres = 100; /* but never more often than once every 100
                                 * connections. */
    }
    else
        heartbeatres = 0;

#ifdef USE_SSL
#ifdef RSAREF
    R_malloc_init();
#else
#if OPENSSL_VERSION_NUMBER < 0x10100000L
    CRYPTO_malloc_init();
#endif
#endif
    SSL_load_error_strings();
    SSL_library_init();
    bio_out=BIO_new_fp(stdout,BIO_NOCLOSE);
    bio_err=BIO_new_fp(stderr,BIO_NOCLOSE);

    if (!(ssl_ctx = SSL_CTX_new(meth))) {
        BIO_printf(bio_err, "Could not initialize SSL Context.\n");
        ERR_print_errors(bio_err);
        exit(1);
    }
    SSL_CTX_set_options(ssl_ctx, SSL_OP_ALL);
#if OPENSSL_VERSION_NUMBER >= 0x10100000L
    SSL_CTX_set_max_proto_version(ssl_ctx, max_prot);
    SSL_CTX_set_min_proto_version(ssl_ctx, min_prot);
#endif
#ifdef SSL_MODE_RELEASE_BUFFERS
    /* Keep memory usage as low as possible */
    SSL_CTX_set_mode (ssl_ctx, SSL_MODE_RELEASE_BUFFERS);
#endif
    if (ssl_cipher != NULL) {
        if (!SSL_CTX_set_cipher_list(ssl_ctx, ssl_cipher)) {
            fprintf(stderr, "error setting cipher list [%s]\n", ssl_cipher);
        ERR_print_errors_fp(stderr);
        exit(1);
    }
    }
    if (verbosity >= 3) {
        SSL_CTX_set_info_callback(ssl_ctx, ssl_state_cb);
    }
#endif
#ifdef SIGPIPE
    apr_signal(SIGPIPE, SIG_IGN);       /* Ignore writes to connections that
                                         * have been closed at the other end. */
#endif
#ifdef _WAF_BENCH_ // restore to no color mode 
    fprintf(stderr,"\033[0m"); // no color
#endif // _WAF_BENCH_ // restore to no color mode 
    copyright();
    test();
#ifdef _WAF_BENCH_ // close the file handles if they're still opened
    // close file for storing received http messages
    if (g_save_file_fd) {
        save_logfile(NULL, 0);
        apr_file_close(g_save_file_fd);
    }
#endif //_WAF_BENCH_ , close the file handles if they're still opened

    apr_pool_destroy(cntxt);

    return 0;
}

