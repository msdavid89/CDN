#!/usr/bin/python
import sys
import socket
import struct
import argparse
from random import randint
import thread

class CDNLogic:

    def __init__(self):
        self.EC2_HOSTS = {'ec2-54-166-234-74.compute-1.amazonaws.com':'54.166.234.74',
             'ec2-52-90-80-45.compute-1.amazonaws.com':'52.90.80.45',
             'ec2-54-183-23-203.us-west-1.compute.amazonaws.com':'54.183.23.203',
             'ec2-54-70-111-57.us-west-2.compute.amazonaws.com':'54.70.111.57',
             'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com':'52.215.87.82',
             'ec2-52-28-249-79.eu-central-1.compute.amazonaws.com':'52.28.249.79',
             'ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com':'54.169.10.54',
             'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com':'52.62.198.57',
             'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com':'52.192.64.163',
             'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com':'54.233.152.60'}
        self.coords = {'54.166.234.74':[],
                       '52.90.88.45':[],
                       '54.183.23.203':[],
                       '54.70.111.57':[],
                       '52.215.87.82':[],
                       '52.28.249.79':[],
                       '54.169.10.54':[],
                       '52.62.198.57':[],
                       '52.192.64.163':[],
                       '54.233.152.60':[]}

    def find_best_replica(self, client_addr):
        return '54.233.152.60'

    


class Packet:
    """
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
    /                     QNAME                     /
    /                                               /
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QTYPE                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QCLASS                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    Answer
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                                               |
    /                                               /
    /                      NAME                     /
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TYPE                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     CLASS                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TTL                      |
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                   RDLENGTH                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
    /                     RDATA                     /
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

    def reset(self):
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
        self.qname = domain
        packet = struct.pack('!HHHHHH', self.id, self.flags, self.qcount,
                             self.acount, self.nscount, self.arcount)
        packet += ''.join(chr(len(x)) + x for x in self.qname.split('.'))
        packet += '\x00'
        packet += struct.pack('!HH', self.qtype, self.q_class)
        return packet


    def generate_answer(self, domain, ip_addr):
        self.acount = 1
        self.flags = 0x8180
        packet = self.generate_question(domain)
        self.aname = 0xC00C
        self.atype = 0x0001
        self.a_class = 0x0001
        self.ttl = 60
        self.data = ip_addr
        self.length = 4
        packet += struct.pack('!HHHLH4s', self.aname, self.atype, self.a_class,
                          self.ttl, self.length, socket.inet_aton(self.data))
        return packet


    def parse_question(self, packet):
        [self.id, self.flags,
         self.qcount, self.acount,
         self.nscount, self.arcount] = struct.unpack('!6H', packet[0:12])
        [self.qtype, self.q_class] = struct.unpack('!HH', packet[-4:])

        name = packet[12:-4]
        i = 0
        tmp = []
        while True:
            k = ord(name[i])
            if k == 0:
                break
            i += 1
            tmp.append(name[i:i+k])
            i += k
        self.qname = '.'.join(tmp)


class DNSServer:
    def __init__(self, port, name):
        self.cdn_logic = CDNLogic()
        self.client_locations = {}
        self.sock = -1
        self.port = port
        self.name = name
        self.my_ip = self.get_ipaddr()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.my_ip, self.port))
        except:
            sys.exit("Failed to create socket.")

    def get_ipaddr(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('cs5700cdnproject.ccs.neu.edu', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def run_server(self):
        while True:
            try:
                request, client = self.sock.recvfrom(65535)
                thread.start_new_thread(self.handle_request, request, client)
            except:
                sys.exit("Error receiving data or creating thread.")
        #self.sock.close()

    def handle_request(self, request, client):
        packet = Packet()
        packet.parse_question(request)

        if client[0] in self.client_locations:
            best_server = self.client_locations[client[0]]
        else:
            best_server = self.cdn_logic.find_best_replica(client[0])

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