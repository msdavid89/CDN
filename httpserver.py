#!/usr/bin/python
import sys
import socket
import argparse
import thread
from threading import RLock
import os
import requests
#import json
import csv
from urllib import quote

MAX_CACHE = 9 * 1024 * 1024  # May need to adjust this, but assume we have 9 MB available


class CacheHandler:
    def __init__(self, dns_port):
        self.dns_port = dns_port
        self.cache = {}  # Dictionary of file path: file size
        self.popularity = {} # Dictionary of file path: popularity as # of hits from CSV
        self.constraints = {} # Dictionary of file path: (size, popularity) for cached pages
        self.available_space = MAX_CACHE
        self.cache_directory = os.getcwd() + '/wiki_cache'
        self.cache_lock = RLock()
        #self.cache_lock = thread.allocate_lock()
        self.space_lock = thread.allocate_lock()
        self.constraints_lock = thread.allocate_lock()
        self.load_local_cache(self.cache_directory)
        self.load_popularity_from_csv()
        #try:
            # Create socket for DNS Server connection, used for active measurements
            # and/or passing cache info to DNS server.
        #    self.dns_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #    self.dns_sock.connect(('cs5700cdnproject.ccs.neu.edu', self.dns_port))
        #    self.dns_sock_lock = thread.allocate_lock()
        #except:
        #    sys.exit("Failed to connect to DNS Server.")
        #self.handle_dns()
        self.update_constraints()

    def handle_dns(self):
        """The thread in this function will be passing caching info
            to the DNS Server so that the DNS Server can pick the best replicas.
        
        try:
            received = self.dns_sock.recv(65535)
            print(received)
            self.popularity = json.loads(received, object_hook=self.decode_json)
        except:
            # Failed to receive popularity from replica
            print("failed to get popularity from DNS Server.")

        print(self.popularity)
        """
        pass

    def load_popularity_from_csv(self):
        """Fills in the popularity dictionary using a CSV file with names and hit rates."""
        try:
            csv_file = open('cdn_popularity.csv', 'r')
        except:
            print("Failed to open csv popularity file (cdn_popularity.csv).")
            return False
        try:
            reader = csv.reader(csv_file)
            for row in reader:
                # Store the site in URL encoded format using urllib.quote
                self.popularity[quote(row[0], safe="/'()")] = int(row[1])
            csv_file.close()
        except:
            print("Failed to load popularity dictionary from CSV.")


    def load_local_cache(self, path):
        """This is used to restore the cache dictionary when the server is restarted."""
        if not os.path.exists(path):
            os.mkdir(path)
            os.mkdir(path + '/wiki')
            return
        for f in os.listdir(path):
            file_name = path + '/' + f
            if os.path.isdir(file_name):
                self.load_local_cache(file_name)
            elif os.path.isfile(file_name):
                size = os.path.getsize(file_name)
                self.space_lock.acquire()
                if self.available_space < size:
                    # remove this file
                    self.space_lock.release()
                    os.remove(file_name)
                else:
                    self.space_lock.release()
                    self.cache_lock.acquire()
                    self.cache[file_name] = size
                    self.cache_lock.release()
                    self.space_lock.acquire()
                    self.available_space -= size
                    self.space_lock.release()


    def update_cache(self, path, contents):
        """Entry point for HTTP Server code. Checks the size available and adds file
            to cache if possible."""
        size = len(contents)
        self.space_lock.acquire()
        if size <= self.available_space:
            self.space_lock.release()
            self.add_to_cache(self.cache_directory + path, contents)
        else:
            self.space_lock.release()
            self.knapsack(path, contents, size)
        self.update_constraints()

    def update_constraints(self):
        """Update the constraints dictionary to reflect size:popularity of currently cached
            content for use in caching algorithm."""
        self.cache_lock.acquire()
        view_only_cache = self.cache.copy()
        self.cache_lock.release()
        self.constraints_lock.acquire()
        for path in view_only_cache.keys():
            pos = path.rfind('/') + 1 # Find the position where the file name begins
            page = path[pos:]
            try:
                self.constraints[path] = (view_only_cache[path], self.popularity[page])
            except:
                print("Error updating constraints for path: " + path + " and page: " + page)
        self.constraints_lock.release()

    def knapsack(self, path, contents, size):
        """Find the lowest cumulative popularity of files in cache which can be removed in
            order to make room for the potential new cache file. Decide if it is worthwhile
            to remove those files.
            
            Note: This is a solution to the knapsack problem
        """

        # Add new path using constraints dictionary so that cache_items provides a full list
        # for cache optimization subject to knapsack problem.
        pos = path.rfind('/') + 1
        page = path[pos:]
        if page == '':
            return False
        self.constraints_lock.acquire()
        cache_items = self.constraints.items()
        self.constraints_lock.release()
        cache_items.append((path, (size, self.popularity[page])))
        cache_items = tuple(cache_items)

        new_cache = {}
        solution = self.solve_knapsack(cache_items, new_cache, MAX_CACHE)
        solution = dict(solution)
        #print("----solution----\n" + str(solution))

        self.cache_lock.acquire()
        try:
            for x in self.cache.keys():
                if x not in solution:
                    # Remove any cached items that are suboptimal
                    print("Removing from cache: " + x)
                    self.remove_from_cache(x)
            if path in solution:
                # Add new page to cache if optimal
                print("Adding to cache: " + path)
                self.add_to_cache(self.cache_directory + path, contents)
        except:
            print("Failed to optimize cache in knapsack.")
        finally:
            self.cache_lock.release()


    def solve_knapsack(self, cache_items, new_cache, maximum):
        """This is the recursive knapsack solving algorithm"""
        if not cache_items:
            return ()
        if (cache_items, maximum) not in new_cache:
            head = cache_items[0]
            tail = cache_items[1:]
            include = (head,) + self.solve_knapsack(tail, new_cache, maximum - head[1][0])
            dont_include = self.solve_knapsack(tail, new_cache, maximum)
            if self.total_popularity(include) > self.total_popularity(dont_include):
                answer = include
            else:
                answer = dont_include
            new_cache[(cache_items, maximum)] = answer
        return new_cache[(cache_items, maximum)]

    def total_popularity(self, values):
        """Helper function for knapsack solution. Returns total popularity of a possible
            cache."""
        total_size = 0
        total_pop = 0
        for v in values:
            total_size += v[1][0]
            total_pop += v[1][1]
        return total_pop if total_size <= MAX_CACHE else 0

    def check_cache(self, path):
        """Checks if a given path is already saved in our cache. If so, return true. Doesn't
            worry about thread safety because if the path is removed from the cache, there
            is a safeguard in remove_from_cache()."""
        path = self.cache_directory + path
        if path in self.cache:
            return True
        return False

    def add_to_cache(self, path, contents):
        """Saves a new file to the cache, returning True if successful. Saves the contents
            of a given file to the location specified by path."""
        try:
            f = open(path, 'w')
            f.write(contents)
            f.close()
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
                self.cache_lock.release()
                if self.space_lock.locked():
                    self.space_lock.release()
                return False
        except:
            print("Failed to write file %s to disk" % path)
            return False

        return True

    def read_from_cache(self, path):
        """Once we know a file exists in the cache, read that file from its path and
            return its contents."""
        path = self.cache_directory + path
        try:
            file = open(path, 'r')
            contents = file.read()
            file.close()
            size = len(contents)
            print("Size of %s: %d" % (path, size))
            return contents, size
        except:
            print("Error reading file from cache.")
            return '', 0

    def remove_from_cache(self, path):
        """Given a file path, remove that file from the disk cache and update space available."""
        try:
            size = os.path.getsize(path)
            os.remove(path)
            self.cache_lock.acquire()
            del self.cache[path]
            self.cache_lock.release()
            self.space_lock.acquire()
            self.available_space += size
            self.space_lock.release()
        except:
            self.cache_lock.release()
            if self.space_lock.locked():
                self.space_lock.release()
            sys.exit("Error removing file from cache.")


class HTTPServer:
    def __init__(self, port, origin):
        self.port = port
        self.origin = origin
        self.cache = CacheHandler(self.port)
        try:
            # Create socket that connects replica to origin server
            self.origin_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.origin_sock.connect((self.origin, 8080))
        except:
            sys.exit("Failed to connect to origin server.")
        try:
            # Create socket for connecting to clients making HTTP requests
            self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.serv_sock.bind(('', self.port))
            self.serv_sock.listen(30)
        except:
            sys.exit("Failed to create socket.")


    def run_server(self):
        """Accept new connections, and pass the new socket and client address to
            a new thread to handle the HTTP requests."""
        while True:
            try:
                cli_sock, addr = self.serv_sock.accept()
                thread.start_new_thread(self.connection_handler, (cli_sock,))
            except:
                # 'Elegantly' shut down, particularly
                thread.interrupt_main()
                sys.exit("Error accepting connection.")


    def connection_handler(self, sock):
        """Manage the connection with a given client."""
        try:
            data = sock.recv(4096)
            path = ''
            lines = data.splitlines()
            for line in lines:
                if "GET " in line:
                    # Find the path of the file the client is requesting
                    path = line.split()[1]
                    if path == '/':
                        # Asking for a directory, which we don't serve.
                        sock.close()
                        return
                    break
        except:
            sys.exit("Error receiving data from client socket.")

        # We now know the file the client is requesting, so we need to see if it is in
        # our cache. If so, send it back. If not, request it from the origin server.
        if self.cache.check_cache(path):
            # Get content from cache, construct HTTP response and send it to the client.
            content, length = self.cache.read_from_cache(path)
            if content != '' and length != 0:
                response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: '
                response += str(length) + '\r\n\r\n' + content
                try:
                    sock.sendall(response)
                except:
                    sys.exit("Failed to send cached response to client.")
                finally:
                    sock.close()
                    return
        if not self.cache.check_cache(path):
            # Request content from origin server, send 404 error if necessary, and decide
            # whether to cache new content or not.
            url = 'http://' + self.origin + ':8080' + path
            r = requests.get(url)
            if r.status_code == 200:
                response = 'HTTP/1.1 200 OK\r\n'
                headers = r.headers.items()
                for h in headers:
                    # Add the origin's response's headers to my response. Need to adjust
                    # content length returned from origin to reflect actual size of file.
                    if h[0] != 'Content-Length':
                        response += str(h[0]) + ': ' + str(h[1]) + '\r\n'
                    else:
                        c = str(r.content)
                        length = len(c)
                        response += 'Content-Length: ' + str(length) + '\r\n'
                response += '\r\n'
                response += r.content
                try:
                    sock.sendall(response)
                except:
                    print("Path where send failed: " + path)
                print("PATH: " + path)
                thread.start_new_thread(self.cache.update_cache, (path, r.content))
            elif r.status_code == 404:
                print("-----404 error------")
                response = 'HTTP/1.1 404 Not Found\r\n'
                try:
                    sock.sendall(response)
                except:
                    print("Path where send failed: " + path)
            else:
                print("---not 200 or 404---")
                response = 'HTTP/1.1 404 Not Found\r\n'
                try:
                    sock.sendall(response)
                except:
                    print("Path where send failed: " + path)

        sock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HTTP Server')
    parser.add_argument('-p', dest='port', type=int)
    parser.add_argument('-o', dest='origin')
    # Origin should be: 'ec2-54-166-234-74.compute-1.amazonaws.com'
    args = parser.parse_args()
    server = HTTPServer(args.port, args.origin)
    server.run_server()
