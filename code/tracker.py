import os, sys, threading, time, json
from socket import *

if __name__ == "__main__":
	DEBUG = True
	chunkId = 0
	peers = [] 
	trackerSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	trackerSocket.bind(('', 0))
	trackerSocket.listen(8)
	trackerPort = trackerSocket.getsockname()[1]
	with open('port.txt', 'w') as f:
		f.write(str(trackerPort))
	if DEBUG: print('TRACKER_PORT=' + str(trackerPort))
	peerLock = threading.Lock()
	ioLock = threading.Lock()

# class Chunk:
# 	def __init__(self, filename, lastChunk):
# 		self.filename = filename
# 		self.lastChunk = lastChunk
# 		self.peersWithMe = [] ## list of {peerId, IP, Port}

class Peer:
	def __init__(self, id, ip, port, filename, filesize, numchunks):
		self.id = id
		self.ip = ip
		self.port = port
		self.filename = filename
		self.filesize = filesize
		self.numchunks = int(numchunks) ## chunks of original file 
		self.files = {filename: {'numchunks': numchunks, 'ip': ip, 'port': port}}

def signalConnectedPeer(peerId, connectionSocket, peerAddr):
	while True:
		for peer in peers:
			peerInfo = json.dumps(peer.files)
			connectionSocket.send(peerInfo.encode())
			peerResponse = connectionSocket.recv(1024).decode()
			peerResponse = json.loads(peerResponse)
			with peerLock: 
				peer.files[peerResponse['filename']] = {
					'numchunks': peerResponse['numchunks'],
					'ip': peerResponse['ip'],
					'port': peerResponse['port']
					} 
				print ('_________________________________________')
				for f in peer.files:
					print (f+": "+str(peer.files[f]['numchunks']))
				# print(str(peer.id)+json.dumps(peer.files))
	connectionSocket.close()

def peerConnect():
	peerId = 100
	while True:
		connectionSocket, peerAddr = trackerSocket.accept()
		initialPeerData = connectionSocket.recv(1024).decode()
		initialPeerData = json.loads(initialPeerData)
		peerFileSize = initialPeerData.get('filesize')
		newPeer = Peer(peerId, peerAddr[0], initialPeerData['port'], initialPeerData['filename'], peerFileSize, \
			int(peerFileSize/512)) 
		with ioLock: print('PEER '+str(peerId)+' CONNECT: OFFERS '+ str(initialPeerData['totalFiles']))
		connectionSocket.send(bytes(str(peerId).encode()))
		with peerLock:
			peers.append(newPeer)
		
		signalConnectedPeerThread = threading.Thread(name="SIGNAL CONNECTED PEER", target=signalConnectedPeer, args=(peerId, connectionSocket, peerAddr))
		peerId += 1 
		signalConnectedPeerThread.start()


if __name__ == "__main__":
	connectionThread = threading.Thread(name='PEER CONNECT', target=peerConnect)
	connectionThread.start()