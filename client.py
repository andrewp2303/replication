import socket
import sys
import select
from termcolor import colored
import threading

def conn_threads(conn):

    # Main loop for clients to receive and send messages to the server.
    while True:   
        # List of input streams.
        sockets_list = [sys.stdin, conn]

        # Initialize read sockets to process inputs from the server.
        read_sockets, _, _ = select.select(
            sockets_list, [], [])

        for socks in read_sockets:

            # Display messages received from the server.
            if socks == conn:
                msg = socks.recv(4096)
                print(msg.decode('UTF-8'))

            # Send requests to the server from the client.
            else:
                msg = sys.stdin.readline().strip()
                conn.send(msg.encode('UTF-8'))
                data = conn.recv(4096)
                print(str(data.decode('UTF-8')))

def Main():
    servers = [None, None, None]

    for i in range(3):
        # Create a TCP socket connection.
        servers[i] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servers[i].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Connect to the servers at the appropriate IP address. 
        if (i == 0): 
            servers[i].connect(("localhost", 5050))

        elif (i == 1): 
            servers[i].connect(("localhost", 5051))

        elif (i == 2):
            servers[i].connect(("localhost", 5052))

    # Welcome message.
    msg = "\nWelcome to the chat application! Begin by logging in or creating an account. Below, you will find a list of supported commands :\n"
    msg += "\nCreate an account.        c|<username>"
    msg += "\nLog into an account.      l|<username>"
    msg += "\nSend a message.           s|<recipient_username>|<message>"
    msg += "\nFilter accounts.          f|<filter_regex>"
    msg += "\nDelete your account.      d|<confirm_username>"
    msg += "\nList users and names.     u"
    msg += "\nUsage help (this page).   h\n"
    msg = colored(msg, 'yellow')
    print(msg)
 
    
    listener1 = threading.Thread(target=conn_threads, args=(servers[0],))
    listener2 = threading.Thread(target=conn_threads, args=(servers[1],))
    listener3 = threading.Thread(target=conn_threads, args=(servers[2],))

    listener1.start()
    listener2.start()
    listener3.start()

    listener1.join()
    listener2.join()
    listener3.join()

if __name__ == '__main__':
    Main()
