import socket, sys
from _thread import *
import re
from termcolor import colored
import threading
import time
from server import *
from client import *
import unittest
import warnings
from collections import deque
import os
import csv, multiprocessing

DIR = 'test_logs'


class PersistentTest(unittest.TestCase):

    # Convert a csv file to a list of its lines
    def csv_to_list(self, filename):
        rows = []
        with open(filename, 'r', newline='') as f:
            csvreader = csv.reader(f)
            for row in csvreader:
                rows.append(row)
        return rows
    
    # Start three server processes for our replicated system.
    def setup(self):
        # Defining stop events for servers. 
        self.stop_event_server1 = multiprocessing.Event()
        self.stop_event_server2 = multiprocessing.Event()
        self.stop_event_server3 = multiprocessing.Event()
                
        self.server1 = Server("localhost", 5050, self.stop_event_server1)
        self.server2 = Server("localhost", 5051, self.stop_event_server2)
        self.server3 = Server("localhost", 5052, self.stop_event_server3)

    # Test that save correctly saves accounts to a persistent store.
    def test_accounts(self):
        self.port = 5050
        self.pending_messages = {}
        self.accounts = ["jim", "varun"]

        self.save()

        self.assertTrue(self.inside_csv_list("jim", self.csv_to_list("5050users.csv")))
        self.assertTrue(self.inside_csv_list("varun", self.csv_to_list("5050users.csv")))

    # Test that save correctly saves messages to a persistent store.
    def test_msg_queue(self):
        self.port = 5050
        self.pending_messages = {"jim": ["hello", "goodbye"], "varun": []}
        self.accounts = ["jim", "varun"]

        # Check that the server adds jim and varun as accounts to the data store.
        self.save()

        self.assertTrue(self.inside_csv_list("hello", self.csv_to_list("5050.csv")))
        self.assertTrue(self.inside_csv_list("goodbye", self.csv_to_list("5050.csv")))

    # Test that accounts retrieved from a store are persistent.
    def test_unpack_accounts(self):
        self.port = 5050
        self.pending_messages = {"jim": ["hello", "goodbye"], "varun": []}
        self.accounts = ["jim", "varun"]
        self.save()

        self.accounts = []

        self.unpack()
        self.assertIn("jim", self.accounts)
        self.assertIn("varun", self.accounts)

    # Test that messages retrieved from a store are persistent.
    def test_unpack_messages(self):
        self.port = 5050
        self.pending_messages = {"jim": ["hello", "goodbye"], "varun": []}
        self.accounts = ["jim", "varun"]
        self.save()

        self.pending_messages = {}

        self.unpack()
        self.assertIn("hello", self.pending_messages["jim"])
        self.assertIn("goodbye", self.pending_messages["jim"])
        self.assertFalse(self.pending_messages.get("varun"))

    # Check if a target is inside a csv in list form.
    def inside_csv_list(self, target, arr):
        for lst in arr:
            if target in lst:
                return True
        return False

    # Clone of the save method from the Server class.
    def save(self):
        """Save accounts and the message queue to csv files."""
        port_csv = f"{self.port}.csv"
        with open(port_csv, 'w') as f:
            for key in self.pending_messages.keys():
                queue = self.pending_messages[key]
                for msg in queue:
                    f.write(f"{key},{msg}\n")

        port_users_csv = f"{self.port}users.csv"
        with open(port_users_csv, 'w') as f:
            for account in self.accounts:
                f.write(f"{account}\n")

    # Clone of the unpack method from the Server class.
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

        

if __name__ == '__main__':
    unittest.main()