#!/usr/bin/python
# Origin Server: ec2-54-166-234-74.compute-1.amazonaws.com

"""        self.EC2_HOSTS = {
             'ec2-52-90-80-45.compute-1.amazonaws.com': '52.90.80.45',
             'ec2-54-183-23-203.us-west-1.compute.amazonaws.com': '54.183.23.203',
             'ec2-54-70-111-57.us-west-2.compute.amazonaws.com': '54.70.111.57',
             'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com': '52.215.87.82',
             'ec2-52-28-249-79.eu-central-1.compute.amazonaws.com': '52.28.249.79',
             'ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com': '54.169.10.54',
             'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com': '52.62.198.57',
             'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com': '52.192.64.163',
             'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com': '54.233.152.60'}

        self.replica_caches = {
                       '52.90.80.45': {}, # N. Virginia
                       '54.183.23.203': {}, # N. California
                       '54.70.111.57': {}, # Oregon
                       '52.215.87.82': {}, # Ireland
                       '52.28.249.79': {}, # Frankfurt
                       '54.169.10.54': {}, # Singapore
                       '52.62.198.57': {}, # Sydney
                       '52.192.64.163': {}, # Tokyo
                       '54.233.152.60': {}} # Sao Paolo
        self.replica_cache_lock = thread.allocate_lock()

"""



import sys
import socket
import struct
import argparse
from random import randint, choice
import thread
import json
import re
import requests
import csv

# Regular Expressions for private network address check
lo = re.compile("^127\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
p_24 = re.compile("^10\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
p_20 = re.compile("^192\.168\.\d{1,3}.\d{1,3}$")
p_16 = re.compile("^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{1,3}.[0-9]{1,3}$")

class CDNLogic:

    def __init__(self, port, ip_addr):
        self.coords = {
                       '52.90.80.45': [39.0437,-77.4875], # N. Virginia
                       '54.183.23.203': [37.7749,-122.4194], # N. California
                       '54.70.111.57': [45.5234,-122.6762], # Oregon
                       '52.215.87.82': [53.3440,-6.2672], # Ireland
                       '52.28.249.79': [50.1155,8.6842], # Frankfurt
                       '54.169.10.54': [1.2897,103.8501], # Singapore
                       '52.62.198.57': [-33.8679,151.2073], # Sydney
                       '52.192.64.163' :[35.6895,139.6917], # Tokyo
                       '54.233.152.60' :[-23.5475,-46.6361]} # Sao Paolo
        self.port = port
        self.my_ip = ip_addr
        #self.popularity = {} # Dictionary of file paths : popularity in hits
        #self.load_popularity_from_csv()
        #try:
        #    self.replica_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #    self.replica_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #    self.replica_sock.bind((self.my_ip, self.port))
        #    self.replica_sock.listen(10)
        #    thread.start_new_thread(self.http, ())
        #except:
        #    sys.exit("Failed to create replica server socket.")


    def load_popularity_from_csv(self):
        """Fills in the popularity dictionary using a CSV file with names and hit rates.
        try:
            csv_file = open('cdn_popularity.csv', 'r')
        except:
            print("Failed to open csv popularity file (cdn_popularity.csv).")
            return False
        try:
            reader = csv.reader(csv_file)
            for row in reader:
                self.popularity[row[0]] = int(row[1])
            csv_file.close()
        except:
            print("Failed to load popularity dictionary from CSV.")
        """
        pass

    def http(self):
        """Server loop accepting connections from replicas.
        while True:
            try:
                rep_sock, addr = self.replica_sock.accept()
                thread.start_new_thread(self.http_handler, (rep_sock, addr))
            except:
                sys.exit("Error accepting connection from replica.")
        """
        pass

    def http_handler(self, sock, addr):
        """Handles communication from replica servers. Send them popularity info.
        
        try:
            to_send = json.dumps(self.popularity, ensure_ascii=False)
            print(to_send)
            sock.sendall(to_send)
        except:
            print("Failed to send popularity to " + str(addr))
        """
        pass

    def find_best_replica(self, client_addr):
        """Given a client IP address, finds the best replica server to serve page."""
        # TODO: handle active measurements.
        if self.is_private(client_addr):
            print("Private IP, use random replica.")
            return choice(self.coords.keys())
        else:
            closest_replica = self.geo_IP(client_addr)
            print("\nClosest replica: " + closest_replica)
            return closest_replica

    def is_private(self, client_addr):
        """Returns True if supplied IP address is in a private range:
                    127.0.0.0   - 127.255.255.255
                    10.0.0.0    - 10.255.255.255
                    172.16.0.0  - 172.31.255.255
                    192.168.0.0 - 192.168.255.255
        """
        if lo.match(client_addr) or p_24.match(client_addr) or p_20.match(client_addr) \
                or p_16.match(client_addr):
            return True
        return False


    def geo_IP(self, client_addr):
        """Finds/returns geographically closest replica server to the client."""
        [lat, lon] = self.get_coords(client_addr)
        cli_coords = [lat, lon]
        closest = ''
        min_dist = float('inf')

        for key in self.coords.keys():
            # Check the distance between the client and each replica, and save
            # the minimum/closest replica
            dist = self.calc_distance(cli_coords, self.coords[key])
            if dist < min_dist:
                min_dist = dist
                closest = key
        return closest


    def get_coords(self, client_addr):
        """Returns the latitutde and longitude of an IP address by making a request to
            freegeoip.net"""
        site = 'http://freegeoip.net/json/%s' % (client_addr)
        r = requests.get(site)
        coords_json = r.json()
        latitude = coords_json["latitude"]
        longitude = coords_json["longitude"]
        return latitude, longitude

    def calc_distance(self, cli, replica):
        """Calculates geographic distance between client and replica server using their
            latitude/longitude."""
        a = (cli[0] - replica[0]) ** 2.0
        b = (cli[1] - replica[1]) ** 2.0
        dist = (a+b) ** (1.0/2.0)
        return dist



class Packet:
    """
    Standard defined here: https://tools.ietf.org/html/rfc2929
    Useful info on DNS field values: http://www.zytrax.com/books/dns/ch15/
    
    'The unsigned fields query count (QDCOUNT), answer count (ANCOUNT),
    authority count (NSCOUNT), and additional information count (ARCOUNT)
    express the number of records in each section for all opcodes'
    
      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      ID                       |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |QR|   Opcode  |AA|TC|RD|RA| Z|AD|CD|   RCODE   |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                QDCOUNT/ZOCOUNT                |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                ANCOUNT/PRCOUNT                |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                NSCOUNT/UPCOUNT                |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                    ARCOUNT                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    Query
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                                               |
    /                     QNAME                     / The domain name being queried
    /                                               /
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QTYPE                     | The resource records being requested
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QCLASS                    | The Resource Record(s) class being requested, for instance, internet
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    Answer
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                                               |
    /                                               / Reflects the QNAME of the question 
    /                      NAME                     /
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TYPE                     | The RR type, for example, A or AAAA
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     CLASS                     | The RR class, for instance, Internet
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TTL                      | Measured in seconds
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                   RDLENGTH                    | The length of RR specific data in octets
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
    /                     RDATA                     / Actual Resource Record data (IP address)
    /                                               /
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    """

    def __init__(self):
        self.id = randint(0, 65535)
        self.flags = 0
        self.qcount = 0
        self.acount = 0
        self.nscount = 0
        self.arcount = 0
        self.qname = ''
        self.qtype = 0
        self.q_class = 0
        self.aname = 0
        self.atype = 0
        self.a_class = 0
        self.ttl = 0
        self.length = 0
        self.data = ''

    def debug(self):
        print "ID: %X, Flags: %X" % (self.id, self.flags)
        print "Qcount: %d, Acount: %d, NS: %d, AR: %d" % (self.qcount, self.acount, self.nscount, self.arcount)
        print "Qname: %s, Qtype: %X, Qclass: %X" % (self.qname, self.qtype, self.q_class)
        print "Aname: %X, Atype: %X, Aclass: %X" % (self.aname, self.atype, self.a_class)
        print "TTL: %d, Length: %X, IP: %s" % (self.ttl, self.length, self.data)

    def reset(self):
        """Unclear if this will be used in final submission."""
        self.id = -1
        self.flags = 0
        self.qcount = 0
        self.acount = 0
        self.nscount = 0
        self.arcount = 0
        self.qname = ''
        self.qtype = 0
        self.q_class = 0
        self.aname = 0
        self.atype = 0
        self.a_class = 0
        self.ttl = 0
        self.length = 0
        self.data = ''

    def generate_question(self, domain):
        """Given a domain, generate the query section for the DNS packet, and the 
            common section (at the top of the diagram above)."""
        self.qname = domain
        packet = struct.pack('!HHHHHH', self.id, self.flags, self.qcount,
                             self.acount, self.nscount, self.arcount)
        packet += ''.join(chr(len(x)) + x for x in self.qname.split('.'))
        packet += '\x00'
        packet += struct.pack('!HH', self.qtype, self.q_class)
        return packet


    def generate_answer(self, domain, ip_addr):
        """Given a domain and replica IP address, construct the DNS answer that will
            be sent to the client."""
        self.arcount = 0 # Using dig, this is set to 1, but we want it zero.
        self.acount = 1 # One answer will be returned
        self.flags = 0x8180 # Bits set: QR (query response), RD (recursion desired), RA (recursion available)
        packet = self.generate_question(domain)
        self.aname = 0xC00C # Pointer to qname label: 1100 0000 0000 1100
        self.atype = 0x0001 # The A record for the domain name
        self.a_class = 0x0001 # Internet (IP)
        self.ttl = 60 # 32-bit value
        self.length = 4 # IP address is 32 bits or 4 bytes, but the length field is 16 bits.
        self.data = ip_addr
        packet += struct.pack('!HHHLH4s', self.aname, self.atype, self.a_class,
                          self.ttl, self.length, socket.inet_aton(self.data))
        return packet


    def parse_question(self, packet):
        """After receiving a question, construct a DNS packet data structure that 
            contains the relevant data from that question. The answer is filled in
            later in a call to generate_answer()"""
        [self.id, self.flags,
         self.qcount, self.acount,
         self.nscount, self.arcount] = struct.unpack('!6H', packet[0:12])

        name = packet[12:-4] # This is qname in the DNS packet diagram above.
        i = 0
        tmp = []
        while True:
            k = ord(name[i]) # Convert from Unicode to numeric representation of character
            if k == 0:
                break
            i += 1
            tmp.append(name[i:i+k])
            i += k
        self.qname = '.'.join(tmp)
        # In the next line, we unpack the 4 bytes past the name, excluding the null byte.
        [self.qtype, self.q_class] = struct.unpack('!HH', packet[12+i+1:12+i+1+4])


class DNSServer:
    """This class is the entry point for the program and handles the actual connection."""
    def __init__(self, port, name):
        self.name = name
        self.port = port
        self.my_ip = self.get_ipaddr()
        self.cdn_logic = CDNLogic(self.port, self.my_ip)
        self.client_locations = {} # Stores mappings from clients to their closest replica
        self.sock = -1
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.my_ip, self.port))
        except:
            sys.exit("Failed to create socket.")

    def get_ipaddr(self):
        """Find IP address of the local machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('cs5700cdnproject.ccs.neu.edu', 80)) # cs5700cdnproject.ccs.neu.edu
        ip = s.getsockname()[0]
        s.close()
        return ip

    def run_server(self):
        """Runs in an infinite loop, getting DNS requests from hosts and spawning
            a new thread to actually process the data."""
        while True:
            try:
                request, client = self.sock.recvfrom(65535)
                thread.start_new_thread(self.handle_request, (request, client))
            except:
                sys.exit("Error receiving data or creating thread.")

    def handle_request(self, request, client):
        """Processes the data for a given DNS request/thread. Based on the request,
            choose the best replica server to handle the HTTP request and alert the
            client."""
        packet = Packet()
        packet.parse_question(request)

        if client[0] in self.client_locations:
            best_server = self.client_locations[client[0]]
        else:
            best_server = self.cdn_logic.find_best_replica(client[0])
            self.client_locations[client[0]] = best_server

        dns_response = packet.generate_answer(self.name, best_server)

        try:
            self.sock.sendto(dns_response, client)
        except:
            sys.exit("Failed to send DNS Answer.")

	
if __name__== '__main__':
    parser = argparse.ArgumentParser(description='DNS Server')
    parser.add_argument('-p',dest='port',type=int)
    parser.add_argument('-n',dest='name')
    args = parser.parse_args()
    server = DNSServer(args.port, args.name)
    server.run_server()
