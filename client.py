import socket
import sys
import select
from termcolor import colored
import threading

def check_alive_conns(conn_list):
    alive_conns = []
    for elt in conn_list: 
        try:
            elt.send(b"")
            alive_conns.append(elt)
        except:
            continue
    return alive_conns

def Main():
    conn1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn1.connect(("localhost", 5050))

    conn2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn2.connect(("localhost", 5051))

    conn3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn3.connect(("localhost", 5052))

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
    
    # Main loop for clients to receive and send messages to the server.
    while True:   
        alive_conns = check_alive_conns([conn1, conn2, conn3])
        curr_conn = alive_conns[0]

        # List of input streams.
        sockets_list = [sys.stdin, curr_conn]

        # Initialize read sockets to process inputs from the server.
        read_sockets, _, _ = select.select(sockets_list, [], [])

        for socks in read_sockets:
            # Display messages received from the server.
            if socks == curr_conn:
                msg = socks.recv(4096)
                print(msg.decode('UTF-8'))

            # Send requests to the server from the client.
            else:
                msg = sys.stdin.readline().strip()
                curr_conn.send(msg.encode('UTF-8'))
                data = curr_conn.recv(4096)
                print(str(data.decode('UTF-8')))

if __name__ == '__main__':
    Main()
