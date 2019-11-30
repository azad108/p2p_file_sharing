import os, sys, threading, time
from socket import *


peerId = 100

class Peer:
	def __init__(self, id, filesize, numchunks):
		self.id = id
		self.filesize = filesize
		self.numchunks = numchunks

trackerSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
trackerSocket.bind(('', 0))
trackerSocket.listen(1) 
trackerPort = trackerSocket.getsockname()[1]
with open('port.txt', 'w') as f:
	f.write(str(trackerPort))


print('TRACKER_PORT=' + str(trackerPort))

while True:
	connectionSocket, peerAddr = trackerSocket.accept()
	peerFilesize = int(connectionSocket.recv(64).decode())
	print(str(peerFilesize))
	print ("connectionSocket= " + str(connectionSocket))
	newPeer = Peer(peerId, peerFilesize, peerFilesize/512) 
	connectionSocket.send(bytes(str(peerId).encode())) 
	peerId += 1

	break