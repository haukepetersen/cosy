#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from os import path
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class HTTPHandler(BaseHTTPRequestHandler):

    index = ''
    root = ''

    def do_GET( self ):
        if self.path == '/':
            req = self.root + '/' + self.index;
        else:
            req = self.root + self.path

        if not path.isfile(req):
            self.send_error(404, 'file not found')
            return

        self.send_response(200)
        if req.endswith('.html'):
            self.send_header('Content-type', 'text/html')
        elif req.endswith('.css'):
            self.send_header('Content-type', 'text/css')
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()

        f = open(req);
        self.wfile.write(f.read())
        f.close()

def run( root, port, index ):
    HTTPHandler.index = index
    HTTPHandler.root = root
    httpd = HTTPServer(('', port), HTTPHandler)
    print("Started frontend server, connect you browser to http://localhost:" + str(port))
    httpd.serve_forever()
