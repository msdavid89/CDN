#!/usr/bin/python
import sys, getopt
import subprocess
#list of all replica severs
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
    port_no = '' #Port number to run the server on
    origin_server = '' 
    cdn_server = 'cs5700cdnproject.ccs.neu.edu'
    RSA_key = '' #path to the RSA to p.key 
    username = '' 
#all info will be gotten from the comand line except  cdn_server.

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:o:n:u:i:h" ,["help"])
    except getopt.GetoptError:
        print "./[deploy|run|stop]CDN -p <port_no> -o <origin> -n <name> -u <username> -i <keyfile>"
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print "./[deploy|run|stop]CDN -p <port_no> -o <origin> -n <name> -u <username> -i <keyfile>"
            sys.exit(1)
        elif opt in ('-p'):
            port_no = arg

        elif opt in ('-o'):
            origin_server = arg

        elif opt in ('-n'):
            resolve_name = arg

        elif opt in ('-u'):
            username = arg

        elif opt in ('-i'):
            RSA_key = arg
#recieve and return command line arguments.
    return port_no, origin_server, cdn_server, username, RSA_key
#this function copies "dnsserver" & 'cdn_popularity.cvs' scripts to the remote host 'cs5700cdnproject.ccs.neu.edu"
def deploy_dns_server(RSA_key, username, cdn_server):
#this is the formated command that does it. 
    command_2 = "scp -i " + RSA_key + "  dnsserver.py  " + " cdn_popularity.cvs "+ username + "@" + cdn_server + ":/home/" + username + "/"
    subprocess.check_output(command_2, shell = True)
#function to copy httpserver script to all replica servers listed above. 
def deploy_http_server(RSA_key, username, replicas_servers):
    for replicas in replicas_servers:
	command_3 = "scp -i "+ RSA_key + " httpserver.py " + username + "@" + replicas + ":"
#	print "deploying to " + replicas
        subprocess.check_output(command_3, shell = True)

if __name__ == '__main__':

    port_no, origin_server, cdn_server, username, RSA_key = validate_args()
    deploy_dns_server(RSA_key, username, cdn_server)
    deploy_http_server(RSA_key, username, replicas_servers)
