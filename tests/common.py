import BaseHTTPServer
import threading


_PORT = 8080


class HTTPServerInstance(object):
    def __init__(self, request_handle = BaseHTTPServer.BaseHTTPRequestHandler):
        self._request_handle = request_handle
    def __enter__(self):
        self._httpd = BaseHTTPServer.HTTPServer(
            ("127.0.0.1", _PORT), 
            self._request_handle)
        thread = threading.Thread(target = self._httpd.serve_forever)
        thread.daemon = True
        thread.start()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._httpd.shutdown()
        self._httpd.server_close()


