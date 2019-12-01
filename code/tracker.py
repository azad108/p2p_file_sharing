import os, sys, threading, time, json
from socket import *

DEBUG = True

chunkId = 0

class Peer:
	def __init__(self, id, ip, port, filename, filesize, numchunks, totalChunks):
		self.id = id
		self.ip = ip
		self.port = port
		self.filename = filename
		self.filesize = filesize
		self.numchunks = numchunks ## chunks of original file
		self.totalChunks = totalChunks ## total chunks all all files

	# def __repr__(self):
	# 	return '{'+str(self.id) + '|' + self.ip + '|' + self.port + '|' + self.filename + '|' \
	# 		+ self.filesize + '|' + self.numchunks + '|' + self.totalChunks + '|'

peers = []


if __name__ == "__main__":
	trackerSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	trackerSocket.bind(('', 0))
	trackerSocket.listen(1) 
	trackerPort = trackerSocket.getsockname()[1]
	with open('port.txt', 'w') as f:
		f.write(str(trackerPort))
	if DEBUG: print('TRACKER_PORT=' + str(trackerPort))
	peerLock = threading.Lock()

# def signalConnectedPeer(index):
# 	for i in range(index):


def peerConnect():
	peerId = 100
	while True:
		connectionSocket, peerAddr = trackerSocket.accept()
		initialPeerData = connectionSocket.recv(1024).decode()
		initialPeerData = json.loads(initialPeerData)
		peerFileSize = initialPeerData.get('filesize')
		newPeer = Peer(peerId, peerAddr[0], peerAddr[0], initialPeerData.get('filename'), peerFileSize, \
			peerFileSize/512, peerFileSize/512)
		print (json.dumps(newPeer.__dict__))
		print('PEER '+str(peerId)+' CONNECT: OFFERS '+ str(initialPeerData.get('totalFiles')))
		connectionSocket.send(bytes(str(peerId).encode()))
		with peerLock:
			peers.append(newPeer)

		peerId += 1 
		break
		# signalConnectedPeerThread = threading.Thread(name="SIGNAL CONNECTED PEER", target=signalConnectedPeer, args=(len(peers)-1),)
		# signalConnectedPeerThread.start()

if __name__ == "__main__":
	connectionThread = threading.Thread(name='PEER CONNECT', target=peerConnect)
	connectionThread.start()
