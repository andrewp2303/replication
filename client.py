import socket
import sys
import select
from termcolor import colored
import threading, multiprocessing

class Client():
    def __init__(self, HOST, PORTS, stop_event):
        self.host = HOST
        self.ports = PORTS
        self.stop_event = stop_event
        self.conns = []
        self.alive_conns = []

        # Form a connection to all of the servers on input ports
        for PORT in PORTS:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                conn.connect((HOST, PORT))
                self.conns.append(conn)
            except:
                print(f"Failed to connect to server at port: {PORT}\n")
        
        # Main loop for clients to receive and send messages to the server.
        while not self.stop_event.is_set():
            # Find currently active replicas, and arbitrarily choose a "primary".   
            self.check_alive_conns()
            self.curr_conn = self.alive_conns[0]

            # List of input streams.
            sockets_list = [sys.stdin, self.curr_conn]

            # Initialize read sockets to process inputs from the server.
            read_sockets, _, _ = select.select(sockets_list, [], [])

            for socks in read_sockets:
                # Display messages received from the "primary" server.
                if socks == self.curr_conn:
                    # If "primary" crashes, try again with a different server.
                    try:
                        msg = socks.recv(4096)
                        print(msg.decode('UTF-8'))
                    except:
                        continue

                # Send requests to all living replicas from the client.
                else:
                    request = sys.stdin.readline().strip()

                    self.send_request(request)

    def send_request(self, request):
        for conn in self.alive_conns:
            conn.send(request.encode('UTF-8'))

            # Only process a response from the "primary" server.
            if conn == self.curr_conn:
                data = conn.recv(4096)
            
        print(str(data.decode('UTF-8')))
    
    def welcome_msg(self):
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

    def check_alive_conns(self):
        '''Pulse each connection to see if if is currently alive.'''
        self.alive_conns = []
        for elt in self.conns: 
            try:
                elt.send(b"")
                self.alive_conns.append(elt)
            except:
                continue

if __name__ == '__main__':

    # Validate command line arguments.
    if len(sys.argv) > 2:
        HOST = sys.argv[1]
        PORTS = [int(sys.argv[i]) for i in range(2, len(sys.argv))]
    else:
        print("Usage: python3 client.py <HOST> <PORT1> <PORT2> ...")
        sys.exit(1)

    stop_event_client = multiprocessing.Event()
    Client(HOST, PORTS, stop_event_client)
