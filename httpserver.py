#!/usr/bin/python
import sys
import socket
import argparse
import thread
import os
import requests

MAX_CACHE = 9 * 1024 * 1024  # May need to adjust this, but assume we have 9 MB available


class CacheHandler:
    def __init__(self):
        self.cache = {}  # Dictionary of file path: file size
        self.available_space = MAX_CACHE
        self.cache_directory = os.getcwd() + '/wiki/'
        self.cache_lock = thread.allocate_lock()
        self.space_lock = thread.allocate_lock()

    def update_cache(self, path, contents):
        """Entry point for HTTP Server code. Checks the size available and adds file
            to cache if possible."""
        # TODO: Implement caching strategy
        size = len(contents) # This might need to check for 'Content-Length'
                             # or 'Transfer-encoding' headers to figure out
        self.space_lock.acquire()
        if size < self.available_space:
            self.space_lock.release()
            self.add_to_cache(path, contents)


    def check_cache(self, path):
        """Checks if a given path is already saved in our cache. If so, return true."""
        self.cache_lock.acquire()
        if path in self.cache:
            self.cache_lock.release()
            return True
        self.cache_lock.release()
        return False

    def add_to_cache(self, path, contents):
        """Saves a new file to the cache, returning True if successful. Saves the contents
            of a given file to the location specified by path."""
        try:
            dir = os.path.dirname(path)
            os.makedirs(dir)
        except:
            return False  # File may already exist at this path
        try:
            file = open(path, 'w')
            file.write(contents)
            file.close()
            try:
                # Update cache and cache size to reflect new file
                size = os.path.getsize(path)
                self.cache_lock.acquire()
                self.cache[path] = size
                self.cache_lock.release()
                self.space_lock.acquire()
                self.available_space -= size
                self.space_lock.release()
            except:
                return False
        except:
            return False
        return True

    def read_from_cache(self, path):
        """Once we know a file exists in the cache, read that file from its path and
            return its contents."""
        try:
            file = open(path, 'r')
            contents = file.read()
            file.close()
            return contents
        except:
            sys.exit("Error reading file from cache.")

    def remove_from_cache(self, path):
        """Given a file path, remove that file from the disk cache and update space available."""
        try:
            os.remove(path)
            self.cache_lock.acquire()
            self.space_lock.acquire()
            self.available_space += self.cache[path]
            del self.cache[path]
            self.cache_lock.release()
            self.space_lock.release()
        except:
            sys.exit("Error removing file from cache.")


class HTTPServer:
    def __init__(self, port, origin):
        self.port = port
        self.origin = origin
        self.cache = CacheHandler()
        try:
            # Create socket for DNS Server connection, used for active measurements
            self.dns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dns_sock.connect(('cs5700cdnproject.ccs.neu.edu', self.port))
            thread.start_new_thread(self.handle_dns)
        except:
            sys.exit("Failed to connect to DNS Server.")
        try:
            # Create socket that connects replica to origin server
            self.origin_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.origin_sock.connect((self.origin, 8080))
        except:
            sys.exit("Failed to connect to origin server.")
        try:
            # Create socket for connecting to clients making HTTP requests
            self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serv_sock.bind(('', self.port))
            self.serv_sock.listen(10)
        except:
            sys.exit("Failed to create socket.")

    def handle_dns(self):
        """The thread in this function will be passing active measurement info
            to the DNS Server so that the DNS Server can pick the best replicas."""
        while True:
            pass

    def run_server(self):
        """Accept new connections, and pass the new socket and client address to
            a new thread to handle the HTTP requests."""
        while True:
            try:
                cli_sock, addr = self.serv_sock.accept()
                thread.start_new_thread(self.connection_handler, (cli_sock, addr))
            except:
                sys.exit("Error accepting connection or spawning thread for it.")

    def connection_handler(self, sock, addr):
        """Manage the connection with a given client."""
        try:
            data = sock.recv(4096)
            host = ''
            path = ''
            if "Host: " in data:
                pos = data.find("Host: ") + 6
                while not data[pos].isspace():
                    host += data[pos]
                    pos += 1
            if "GET " in data:
                # Find the path of the file the client is requesting
                pos = data.find("GET ") + 4
                while not data[pos].ispace():
                    path += data[pos]
                    pos += 1
        except:
            sys.exit("Error receiving data from client socket.")

        # We now know the file the client is requesting, so we need to see if it is in
        # our cache. If so, send it back. If not, request it from the origin server.
        if self.cache.check_cache(path):
            # Get content from cache, construct HTTP response and send it to the client.
            content = self.cache.read_from_cache(path)
            len = os.path.getsize(path)
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: '
            response += str(len) + '\r\n\r\n' + content
            try:
                sock.sendto(response, addr)
            except:
                sys.exit("Failed to send cached response to client.")
        else:
            # Request content from origin server, send 404 error if necessary, and decide
            # whether to cache new content or not.
            url = 'http://' + self.origin + ':8080' + path
            r = requests.get(url)
            if r.status_code == 200:
                response = 'HTTP/1.1 200 OK\r\n'
                headers = r.headers.items()
                for h in headers:
                    # Add the origin's response's headers to my response
                    response += str(h[0]) + ': ' + str(h[1]) + '\r\n'
                response += '\r\n'
                response += r.content
                self.cache.update_cache(path, r.contents)
            else:
                response = 'HTTP/1.1 404 Not Found'
                sock.sendto(response, addr)

        sock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Server')
    parser.add_argument('-p', dest='port', type=int)
    parser.add_argument('-o', dest='origin')
    # Origin should be: 'ec2-54-166-234-74.compute-1.amazonaws.com'
    args = parser.parse_args()
    server = HTTPServer(args.port, args.origin)
    server.run_server()
