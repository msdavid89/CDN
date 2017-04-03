import sys
import socket
import struct
import argparse
from random import randint

EC2_HOSTS = {'ec2-54-166-234-74.compute-1.amazonaws.com':'54.166.234.74',
             'ec2-52-90-80-45.compute-1.amazonaws.com':'52.90.88.45',
             'ec2-54-183-23-203.us-west-1.compute.amazonaws.com':'54.183.23.203',
             'ec2-54-70-111-57.us-west-2.compute.amazonaws.com':'54.70.111.57',
             'ec2-52-215-87-82.eu-west-1.compute.amazonaws.com':'52.215.87.82',
             'ec2-52-28-249-79.eu-central-1.compute.amazonaws.com':'52.28.249.79',
             'ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com':'54.169.10.54',
             'ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com':'52.62.198.57',
             'ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com':'52.192.64.163',
             'ec2-54-233-152-60.sa-east-1.compute.amazonaws.com':'54.233.152.60'}

class Packet:

    def __init__(self):
        self.id = randint(0, 65535)
        self.flags = 0
        self.qcount = 0
        self.acount = 0
        self.nscount = 0
        self.arcount = 0
        self.question = Question()
        self.answer = Answer()

    def generate_question(self,domain):


    def generate_answer(self,domain,ip_addr):


    def parse(self,packet):
        

class Question:

    def __init__(self):
        self.name = ''
        self.type = 0
        self.q_class = 0

    def pack_question(self,domain):


    def parse_question(self,packet):


class Answer:
    def __init__(self):
        self.name = 0
        self.type = 0
        self.a_class = 0
        self.ttl = 0
        self.length = 0
        self.data = ''

    def generate_answer(self, ip_addr):



class DNSServer:
    def __init__(self):


if __name__== '__main__':
    parser = argparse.ArgumentParser(description='DNS Server')
    parser.add_argument('-p',dest='port',type=int)
    parser.add_argument('-n',dest='name')
    args = parser.parse_args()



