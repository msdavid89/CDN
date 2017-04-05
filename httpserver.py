#!/usr/bin/python
import sys
import socket
import argparse
import thread

class CacheHandler:

	def __init__(self):
		self.cache = []



class HTTPServer:

	def __init__(self, port, origin):
		self.port = port
		self.origin = origin
		self.cache = CacheHandler()
		try:
			self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.serv_sock.bind(('', self.port))
			self.serv_sock.listen(10)
		except:
			sys.exit("Failed to create socket.")

	def run_server(self):
		while True:
			try:
				cli_sock, addr = self.serv_sock.accept()
				thread.start_new_thread(self.connection_handler, cli_sock, addr)
			except:
				sys.exit("Error accepting connection or spawning thread for it.")

	def connection_handler(self, sock, addr):
		data = sock.recv(1024)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='HTTP Server')
	parser.add_argument('-p',dest='port',type=int)
	parser.add_argument('-o',dest='origin')
	args = parser.parse_args()
	server = HTTPServer(args.port, args.origin)
	server.run_server()