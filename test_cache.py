#!/usr/bin/python
import csv
import subprocess
from random import randint
import os
import thread

directory = os.getcwd()
popularity = {}
try:
    csv_file = open('cdn_popularity.csv', 'r')
except:
    print("Failed to open csv popularity file (cdn_popularity.csv).")
try:
    reader = csv.reader(csv_file)
    csv_list = list(reader)
    for row in reader:
        popularity[row[0]] = int(row[1])
    csv_file.close()
except:
    print("Failed to load popularity dictionary from CSV.")


def wget_func(q, p, d):
    try:
        subprocess.check_output(["wget", q])
        to_remove = d + '/' + p
        print(to_remove)
        os.remove(to_remove)
    except:
        print("\n\nQuery: " + q + " returned error.\n\n")


count = 0
while count < 5:
    count += 1
    r = randint(0,4999)
    path = csv_list[r][0]
    query = "http://ec2-52-90-80-45.compute-1.amazonaws.com:40023/wiki/%s" % (path)
    wget_func(query, path, directory)

# wget http://ec2-52-90-80-45.compute-1.amazonaws.com:40009/wiki/Mesut_%C3%96zil