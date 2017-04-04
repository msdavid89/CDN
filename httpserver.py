#!/usr/bin/env python
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler 



def CustomizedHTTPHandler():
        Server = BaseHTTPServer.HTTPServer
	hadl = SimpleHTTPRequestHandler
	server_address = ("172.16.67.170",7711)
	hadl.protocol_version = 'HTTP/1.1'
	httpd = Server(server_address, hadl)
	httpd.serve_forever()

if __name__ == '__main__':
  serv = CustomizedHTTPHandler( )
  serv.start()
