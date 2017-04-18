#!/usr/bin/python
import sys, getopt
import subprocess
#list of replica servers to be used 
replicas_servers = [
"ec2-52-90-80-45.compute-1.amazonaws.com", 
"ec2-54-183-23-203.us-west-1.compute.amazonaws.com", 
"ec2-54-70-111-57.us-west-2.compute.amazonaws.com",
"ec2-52-215-87-82.eu-west-1.compute.amazonaws.com",
"ec2-52-28-249-79.eu-central-1.compute.amazonaws.com", 
"ec2-54-169-10-54.ap-southeast-1.compute.amazonaws.com", 
"ec2-52-62-198-57.ap-southeast-2.compute.amazonaws.com", 
"ec2-52-192-64-163.ap-northeast-1.compute.amazonaws.com", 
"ec2-54-233-152-60.sa-east-1.compute.amazonaws.com"]

def validate_args():
    port = ''
    origin_server = ''
    cdn_server = 'cs5700cdnproject.ccs.neu.edu'
    RSA_key_path = ''
    username = ''
    name = ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:o:n:u:i:h" ,["help"])
    except getopt.GetoptError:
        print "./[deploy|run|stop]CDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile>"
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print "./[deploy|run|stop]CDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile>"
            sys.exit(1)
        elif opt in ('-p'):
            port = arg

        elif opt in ('-o'):
            origin_server = arg

        elif opt in ('-n'):
            name = arg

        elif opt in ('-u'):
            username = arg

        elif opt in ('-i'):
            RSA_key_path = arg

#recieve value from the command line and return.
    return port, origin_server, cdn_server, username, RSA_key_path, name

#function to run sripts (dnsserver) remotely  
def run_dns_server(port, cdn_server, username, RSA_key_path, name):
    run_dns = "ssh -i "+ RSA_key_path +" "+ username + "@" + cdn_server + " nohup" + " python " + "dnsserver.py -p "+ port + " -n "+ name + " &"
    print run_dns
    subprocess.check_output(run_dns, shell=True)


#    print "dnsserver running...."
#function to run httpserver on the replicas(from the lists above).

def run_http_servers(port, origin_server, username, RSA_key_path,):
    for replicas in replicas_servers:
        run_http = "ssh -i "+ RSA_key_path +" "+ username + "@" + replicas + " nohup" + " python " + "httpserver.py -p "+ port + " -o "+ origin_server + " &"
	print run_http
        subprocess.check_output(run_http ,shell=True)
#	print "httpserver running...."

if __name__ == '__main__':

    port, origin_server, cdn_server, username, RSA_key_path, name = validate_args()
    run_dns_server(port, cdn_server, username, RSA_key_path, name)
    run_http_servers(port, origin_server, username, RSA_key_path )
