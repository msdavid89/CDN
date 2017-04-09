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
        self.coords = {'54.166.234.74':[39.0437,-77.4875],
                       '52.90.88.45':[39.0437,-77.4875],
                       '54.183.23.203':[37.7749,-122.4194],
                       '54.70.111.57':[45.5234,-122.6762],
                       '52.215.87.82':[53.3440,-6.2672],
                       '52.28.249.79':[50.1155,8.6842],
                       '54.169.10.54':[1.2897,103.8501],
                       '52.62.198.57':[-33.8679,151.2073],
                       '52.192.64.163':[35.6895,139.6917],
                       '54.233.152.60':[-23.5475,-46.6361]}

    def find_best_replica(self, client_addr):
        return '54.233.152.60'

    


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
        """Find IP address of the local machine."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('cs5700cdnproject.ccs.neu.edu', 80))
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
        #self.sock.close()

    def handle_request(self, request, client):
        """Processes the data for a given DNS request/thread. Based on the request,
            choose the best replica server to handle the HTTP request and alert the
            client."""
        packet = Packet()
        packet.parse_question(request)

        print("Request: " + repr(request))
        packet.debug()

        if client[0] in self.client_locations:
            best_server = self.client_locations[client[0]]
        else:
            best_server = self.cdn_logic.find_best_replica(client[0])
        dns_response = packet.generate_answer(self.name, best_server)

        print('DNS Response: ' + repr(dns_response))
        packet.debug()

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
