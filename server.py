import socket, sys, csv
from _thread import *
import re
from termcolor import colored
import threading, multiprocessing
import time

class Server():
    """Server class for primary and replica servers."""

    def __init__(self, ip, port, stop_event):
        # The IP address of the server running.
        self.ip = ip

        # The port of the server running.
        self.port = port

        # Stores an event that can close the server (used for testing)
        self.stop_event = stop_event

        # A dictionary with username as key and pending messages as values.
        self.pending_messages = {} 

        # How many seconds the server waits before pickling the current queue.
        self.pickle_interval = 1

        # A list of account names.
        self.accounts = []

        # A dictionary with usernames as keys and connection references as values.
        self.conn_refs = {}

        # A dictionary with logged in users.
        self.logged_in = []

        # Retrieve accounts and pending messages from the current queue.
        self.unpack()

        # Specify the address domain and read properties of the socket.
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Connect to the server at the specified port and IP address.
        server.bind((self.ip, self.port))

        # Listen for a maximum of 100 active connections (can be adjusted).
        server.listen(100)

        print(f"Server started, listening on port {self.port}.\n")

        server.settimeout(1)  # Set a timeout for the accept() method

        # Main loop for the server to listen to client requests until timeout.
        while not self.stop_event.is_set():
            try:
                connection, address = server.accept()
                print('\nConnected to:', address[0], ':', address[1])
                start_new_thread(self.wire_protocol, (connection,))
            except socket.timeout:
                continue
        
        # Kill the server if the timeout event is set. 
        server.close()
        print(f"Server stopped, no longer listening on port {self.port}.\n")

    def create_account(self, msg_list, connection):
        """Create an account, and associate with the appropriate socket. (c|<username>)"""

        if len(msg_list) != 2:
            msg = (colored("\nInvalid arguments! Usage: c|<username>\n", "red"))
            return msg

        self.update_live_users()
        init_user = self.get_account(connection)

        if init_user in self.logged_in:
            msg = (colored("\nPlease disconnect first!\n", "red"))
            return msg

        username = msg_list[1]

        if username in self.accounts:
            print(f"\nUser {username} account creation rejected\n")
            msg = colored(f"\nAccount {username} already exists!\n", "red")
            return msg

        if not re.fullmatch("\w{2,20}", username):
            print(f"\nUser {username} account creation rejected\n")
            msg = colored(
                f"\nUsername must be alphanumeric and 2-20 characters!\n", "red")
            return msg

        self.accounts.append(username)
        print(f"\nUser {username} account created\n")
        msg = colored(
            f"\nNew account created! User ID: {username}. Please log in.\n", "green")
        return msg


    def delete_account(self, msg_list, connection):
        """Delete the current user's account. (d|<confirm_username>)"""

        if len(msg_list) != 2:
            msg = (colored("\nInvalid arguments! Usage: d|<confirm_username>\n", "red"))
            return msg

        username = msg_list[1]
        init_user = self.get_account(connection)

        if (init_user != username):
            msg = (colored("\nYou can only delete your own account.\n", "red"))
            return msg

        print(f"\nUser {username} requesting account deletion.\n")

        if username in self.accounts:
            self.accounts.remove(username)
            self.logged_in.remove(username)
            if self.pending_messages.get(username):
                self.pending_messages.pop(username)
            print(f"\nUser {username} account deleted.\n")
            msg = colored(f"\nAccount {username} has been deleted.\n", "green")
            return msg

        else:
            return (colored("\nIncorrect username for confirmation.\n", "red"))


    def update_live_users(self):
        """Check which socket connections are still live."""

        curr_users = []
        for user in self.conn_refs:
            try:
                self.conn_refs[user].send("".encode('UTF-8'))
                curr_users.append(user)
            except:
                pass

        for user in self.logged_in:
            if user not in curr_users:
                self.logged_in.remove(user)


    def list_accounts(self):
        """List all of the registered users and display their status. (u)"""

        print(f'\nListing accounts\n')

        self.update_live_users()

        if self.accounts:
            acc_str = "\n" + "\n".join([(colored(f"{u} ", "blue") +
                                         (colored("(live)", "green") if u in self.logged_in else ""))
                                        for u in self.accounts]) + "\n"

        else:
            acc_str = colored("\nNo existing users!\n", "red")

        return acc_str


    def verify_dupes(self, connection):
        """Verify if a user is already logged in when they try to log in."""

        for username in self.logged_in:
            if self.conn_refs[username] == connection:
                return True
        return False


    def login(self, msg_list, connection):
        """Check that the user is not already logged in, log in to a particular user, and deliver unreceived messages if applicable."""

        if len(msg_list) != 2:
            msg = (colored("\nInvalid arguments! Usage: l|<username>\n", "red"))
            return msg

        check_duplicate = self.verify_dupes(connection)

        if check_duplicate == True:
            msg = (colored("\nPlease log out first!\n", "red"))
            return msg

        username = msg_list[1]

        print(f"\nLogin as user {username} requested\n")

        self.update_live_users()

        if username in self.logged_in:
            print(f"\nLogin as {username} denied.\n")
            msg = colored(
                f"\nUser {username} already logged in. Please try again.\n", "red")
            return msg

        elif username not in self.accounts:
            print(f"\nLogin as {username} denied.\n")
            msg = colored(
                f"\nUser {username} does not exist. Please create an account.\n", "red")
            return msg

        else:
            self.conn_refs[username] = connection
            print(f"\nLogin as user {username} completed.\n")
            msg = colored(
                f"\nLogin successful - welcome back {username}!\n", "green")
            if username in self.pending_messages:
                print(f"\nDelivering pending messages to {username}.\n")
                self.send_msg(connection, username, colored(
                    f"\nYou have pending messages! Delivering the  messages now...", "green"))
                self.deliver_pending_messages(username)
            self.logged_in.append(username)
            return msg


    def get_account(self, connection):
        """Get account from connection refernce by reverse searching the live_users dictionary."""

        for username in self.conn_refs:
            if self.conn_refs[username] == connection:
                return username
        return None


    def deliver_pending_messages(self, recipient_name):
        """Deliver pending messages to a user."""

        while self.pending_messages[recipient_name]:
            self.conn_refs[recipient_name].send(
                self.pending_messages[recipient_name][0].encode('UTF-8'))
            self.pending_messages[recipient_name].pop(0)


    def send_msg(self, connection, recipient_name, msg):
        """Send a message to the given user."""

        print(f"\nRequest received to send message to {recipient_name}.\n")

        self.update_live_users()
        init_user = self.get_account(connection)

        if init_user not in self.logged_in:
            msg = (colored("\nPlease log in to send a message!\n", "red"))
            return msg

        if recipient_name in self.accounts:
            sender_name = self.get_account(connection)
            if recipient_name in self.logged_in:
                msg = colored(f"[{sender_name}] ", "grey") + msg
                self.conn_refs[recipient_name].send(msg.encode('UTF-8'))
                print(f"\nMessage sent to {recipient_name}.\n")
                msg = colored(f"\nMessage sent to {recipient_name}.\n", "green")
            else:
                msg = colored(f"[{sender_name}] ", "grey") + msg
                if recipient_name in self.pending_messages:
                    self.pending_messages[recipient_name].append(msg)
                else:
                    self.pending_messages[recipient_name] = [msg]
                print(
                    f"\nMessage will be sent to {recipient_name} after the account is online.\n")
                msg = colored(
                    f"\nMessage will be delivered to {recipient_name} after the account is online.\n", "green")
            return msg

        else:
            msg = colored(
                "\nMessage failed to send! Verify recipient username.\n", "red")
            print(f"\nRequest to send message to {recipient_name} denied.\n")
            return msg


    def filter_accounts(self, msg_list):
        """Filter accounts by a given regex."""

        print(f'\nFiltering accounts.\n')

        if len(msg_list) != 2:
            msg = (colored("\nInvalid arguments! Usage: f|<filter_regex>\n", "red"))
            return msg

        self.update_live_users()

        fltr = msg_list[1]
        def fun(x): return re.fullmatch(fltr, x)
        filtered_accounts = list(filter(fun, self.accounts))

        if len(list(filtered_accounts)) > 0:
            acc_str = "\n" + "\n".join([(colored(f"{u} ", "blue") +
                                         (colored("(live)", "green") if u in self.logged_in else ""))
                                        for u in filtered_accounts]) + "\n"

        else:
            acc_str = colored("\nNo matching users!\n", "red")

        return acc_str
    
    def save(self):
        """Save accounts and the message queue to csv files."""
        port_csv = f"{self.port}.csv"
        with open(port_csv, 'w') as f:
            for key in self.pending_messages.keys():
                queue = self.pending_messages[key]
                for msg in queue:
                    print(f"Writing pending msg: {self.pending_messages[key]}")
                    f.write(f"{key},{msg}\n")

        port_users_csv = f"{self.port}users.csv"
        with open(port_users_csv, 'w') as f:
            for account in self.accounts:
                f.write(f"{account}\n")

    def unpack(self):
        """Unpack the accounts and message queue from csv files."""
        port_csv = f"{self.port}.csv"
        with open(port_csv, 'r') as f:
            for line in f:
                key, value = line.strip().split(',')
                if self.pending_messages.get(key):
                    self.pending_messages[key].append(value)
                else:
                    self.pending_messages[key] = [value]
        
        port_users_csv = f"{self.port}users.csv"
        with open(port_users_csv, 'r') as f:
            for line in f:
                account = line.strip()
                self.accounts.append(account)

    def wire_protocol(self, connection):
        """Main server thread that continues running until the connection is closed."""

        pickleTime = time.time()
        while True:
            # Ensure persistence by pickling queue at a given interval
            if time.time() > pickleTime + self.pickle_interval:
                print("Saving accounts and messages.\n")
                self.save()
                pickleTime = time.time()
            
            # Preprocess the message by decoding it and splitting it by delimeter.
            msg = connection.recv(4096)
            msg_str = msg.decode('UTF-8')
            msg_list = msg_str.split('|')
            msg_list = [elt.strip() for elt in msg_list]
            op_code = msg_list[0].strip()

            # Create an account.
            # Usage: c|<username>
            if op_code == 'c':
                msg = self.create_account(msg_list, connection)

            # Log into an account.
            # Usage: l|<username>
            elif op_code == 'l':
                msg = self.login(msg_list, connection)

            # List all users and their status.
            # Usage: u
            elif op_code == 'u':
                msg = self.list_accounts()

            # Send a message to a user.
            # Usage: s|<recipient_username>|<message>
            elif op_code == 's':
                if len(msg_list) != 3:
                    msg = (colored(
                        "\nInvalid arguments! Usage: s|<recipient_username>|<message>\n", "red"))
                else:
                    msg = self.send_msg(connection, msg_list[1], msg_list[2])

            # Delete an account
            # Usage: d|<confirm_username>
            elif op_code == 'd':
                msg = self.delete_account(msg_list, connection)

            # Filter accounts using a certain wildcard.
            # Usage: f|<filter_regex>
            elif op_code == 'f':
                msg = self.filter_accounts(msg_list)

            # Print a list of all the commands.
            # Usage: h
            elif op_code == 'h':
                msg = "\nUsage help below:\n"
                msg += "\nCreate an account.        c|<username>"
                msg += "\nLog into an account.      l|<username>"
                msg += "\nSend a message.           s|<recipient_username>|<message>"
                msg += "\nFilter accounts.          f|<filter_regex>"
                msg += "\nDelete your account.      d|<confirm_username>"
                msg += "\nList users and names.     u"
                msg += "\nUsage help (this page).   h\n"
                msg = colored(msg, 'yellow')

            # Handles an invalid request and lists the correct usage for the user.
            else:
                msg = "\nInvalid request, use \"h\" for usage help!\n"
                msg = colored(msg, 'red')

            # Send encoded acknowledgment to the connected client
            connection.send(msg.encode('UTF-8'))

def test_two_fault():
    """Test the two fault tolerance of servers by shutting 2 down."""
    stop_event_server1 = multiprocessing.Event()
    stop_event_server2 = multiprocessing.Event()
    stop_event_server3 = multiprocessing.Event()

    # Creating the server threads. 
    server1 = multiprocessing.Process(target=Server, args=("localhost", 5050, stop_event_server1))
    server2 = multiprocessing.Process(target=Server, args=("localhost", 5051, stop_event_server2))
    server3 = multiprocessing.Process(target=Server, args=("localhost", 5052, stop_event_server3))

    # Starting servers. 
    server1.start()
    server2.start()
    server3.start()

    time.sleep(30)  # Wait for 30 seconds
    stop_event_server1.set()  # Signal server1 to stop.

    # Sleeping for 30 seconds and then shutting down the next server. 
    time.sleep(30)
    stop_event_server2.set()

if __name__ == '__main__':

    # Validate command line arguments.
    if len(sys.argv) == 3:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])
        # Defining stop events for servers. 
        stop_event_server = multiprocessing.Event()

        # Start the server process.
        Server(HOST, PORT, stop_event_server)
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        test_two_fault()
    else:
        print("Usage: python3 server.py <HOST> <PORT>")
        sys.exit(1)
