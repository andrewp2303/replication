
<h1 align="center">
  Client-Server Chat Application
  <br>
</h1>

<h4 align="center">Authored by Adarsh Hiremath and Andrew Palacci</h4>

<p align="center">
  <a href="#key-features">Overview</a> •
  <a href="#setup">Setup</a> •
  <a href="#how-to-use">How to Use</a> 
</p>

## Key Features

* We implemented an end-
to-end client-server chat application, first with our
own wire protocol and later with gRPC. 
* As currently implemented, our chat
application supports the following:
  - Account creation, login, deletion, and disconnection.
  - Sending messages between accounts, even when
  some accounts are offline.
  - Listing or filtering all users who have created
accounts.
* The source code for our chat application can be
found in the main directory here. The gRPC implementation is in grpcApp.
* We have done extensive manual unit testing, as documented in tests.txt 
* You can also find our project writeup at template.pdf
  
## Setup

To clone and run this application, you'll need [Python](https://www.python.org/downloads/release/python-372/). We have a list of requirements which you can find in the requirements.txt file. To install these requirements, run the following in your command line: 

```bash
$ pip3 install -r requirements.txt
```

Next, you'll need to set the appropriate IP address and port number in server.py and client.py (for both the regular implementation and the gRPC implementation).

Run the following command to get your private IP address (on wireless networks): 
```bash
$ ipconfig getifaddr en0
```
Run this command for wired networks: 
```bash
$ ipconfig getifaddr en1
```

Finally, turn off your Firewall so that your machine can accept incoming network connections. 

## How to Use

First, run ```server.py <IP> <PORT>``` using the IP you found above, and then using a port of your choice. In order to ensure 2-fault tolerance, we must do this using 3 different ports (e.g. 3 different machines). This can also be done by running server.py with a test flag --- ```server.py test```. Finally, run ```client.py <IP> <PORT1> <PORT2> <PORT3>``` on all the machines you want to be clients, with the 3 ports representing each of the replica machines.

Congratulations! You've now established a connection between your client and server. You can begin making commands by using the following usage. 

| Syntax | Description |
| --- | ----------- |
| Usage: c &#124; \<username\> | Create an account. |
| Usage: l &#124; \<username\>  | Log into an account. |
| Usage: u | List all users and their activity status. | 
| Usage: s &#124; \<recipient_username\> &#124; \<message\> | Send a message to a user. | 
| Usage: d &#124; \<confirm_username\> | Delete an account. | 
| Usage: f &#124; \<filter_regex\> | Filter accounts using a wildcard. | 
| Usage: h | Print a list of all the commands. |
