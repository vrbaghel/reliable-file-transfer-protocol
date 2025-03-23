# Reliable File Communication Protocol

This repository contains a solution to Reliable File Communication Protocol as a part of Networking course at the University of Illinois (Chicago).

The goal is to implement a reliable file communication protocol over an unreliable network connection. The protocol is supposed to be able to transfer a file from a client to a server over a network connection which may be lossy or have delay. The protocol should be able to detect and recover from lost packets.

The solution is implemented in Python 3.7 and consists of two parts: the client and the server. The client sends the file to the server and the server receives the file. The protocol is implemented using UDP sockets. The reliability is ensured by implementing ACKs (acknowledgments) and retransmission of lost packets.

The repository contains the following files:

- `server.py`: the server side of the protocol
- `sender.py`: the client side of the protocol
- `tester.py`: a script to test the protocol
- `utils/wire.py`: a module to create a UDP socket with loss and delay
- `utils/logging.py`: a module to set up logging
- `utils/utils.py`: a module to read a file and compute its hash
