import os, sys, threading, time, json, math
from socket import *

if __name__ == "__main__":
	DEBUG = False
	chunkId = 0
	peers = []
	files = {}
	trackerSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	trackerSocket.bind(('', 0))
	trackerSocket.listen(8)
	trackerPort = trackerSocket.getsockname()[1]
	with open('port.txt', 'w') as f:
		f.write(str(trackerPort))
	if DEBUG: print('TRACKER_PORT=' + str(trackerPort))
	peerLock = threading.Lock()
	filesLock = threading.Lock()
	ioLock = threading.Lock()  

def signalConnectedPeer(peerId, connectionSocket, peerAddr):
	while True: 
		for fname in files.copy(): ## make sure all peers have all the files
			request = {
				'id': peerId,  # id of the peer that's makinng request
				'filename': fname,
				'peers': files[fname]
				}
			peerInfo = json.dumps(request)
			connectionSocket.send(peerInfo.encode())
			peerResponse = connectionSocket.recv(1024).decode()
			peerResponse = json.loads(peerResponse)
			with filesLock:
				if peerResponse['isClosed'] == 1: 
					numfiles=0
					for file in files: numfiles+=1
					with ioLock: print('PEER '+ str(peerId) +' DISCONNECT: '+'RECEIVED '+str(numfiles))
					for file in files:
						with ioLock: print(str(peerId) + '    ' + file)
						files[file].pop(str(peerId), None)
					if not files[file]: files.pop(file, None)
					connectionSocket.close()
					if DEBUG: print(files)
					return
			files[peerResponse['filename']] = peerResponse['peers']

	


def peerConnect():
	peerId = 100
	while True:
		connectionSocket, peerAddr = trackerSocket.accept()
		initialPeerData = connectionSocket.recv(1024).decode()
		initialPeerData = json.loads(initialPeerData)
		peerFileSize = initialPeerData.get('filesize') 
		with ioLock: 
			print('PEER '+str(peerId)+' CONNECT: OFFERS '+ str(initialPeerData['totalFiles']))
			print(str(peerId) + '    ' + initialPeerData['filename']+ ' ' + str(math.ceil(peerFileSize/512)))
		ackData = {'id': peerId, 'ip': peerAddr[0]}

		connectionSocket.send(json.dumps(ackData).encode())
 
		with filesLock:
			files[initialPeerData['filename']] = {}
			files[initialPeerData['filename']][str(peerId)] = {
					'ip': peerAddr[0], 
					'port': initialPeerData['port'],
					'originalSize': peerFileSize,
					'acquiredSize': peerFileSize
			}
			
		if DEBUG: print(files)
		## peerIds: mapped onto {IP, Port, originalSize, acquiredSize} tuple
		
		signalConnectedPeerThread = threading.Thread(name="SIGNAL CONNECTED PEER", target=signalConnectedPeer, args=(peerId, connectionSocket, peerAddr))
		peerId += 1 
		signalConnectedPeerThread.start()


if __name__ == "__main__":
	connectionThread = threading.Thread(name='PEER CONNECT', target=peerConnect)
	connectionThread.start()