import os, re, sys, threading, time, json
from socket import *
DEBUG = True

if __name__ == "__main__":
	if len(sys.argv) != 4:
	  print("Usage: {} {} {} {}".format(
	    "./peer", "TRACKER_IP", "TRACKER_PORT", "MIN_ALIVE_TIME"))
	  exit(1)
	myFiles = {} ## Dictionary containing all the files that the current 
				 ## peer has in its shared directory
	curPeerData = {}
	trackerAddr = sys.argv[1]
	trackerPort = int(sys.argv[2])
	minAliveTime= sys.argv[3]


	downSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	downSocket.bind(('', 0))
	downSocket.listen(8)
	downPort = downSocket.getsockname()[1]


def requestFiles(peerSocket, countdown):
	global trackerAddr, trackerPort, minAliveTime, upSocket, downSocket
	timedOut = time.time()-countdown >= float(minAliveTime)
	recvdAll = False
	while True:
		if recvdAll: break
		sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
		                       for f in files] 
		for file in sharedDir:
			myFiles[sharedDir[0]] = {
				'id': curPeerData['id'] ,
				'filesize': int(os.path.getsize(file)),
				'numchunks': int(os.path.getsize(file)/512)
			} 
		response = peerSocket.recv(1024).decode()
		filesOffered = json.loads(response)
		for fname in filesOffered:
			if fname in sharedDir:
				chunksProvided = int(filesOffered[fname]['numchunks'])
				chunksAcquired = int(os.path.getsize(fname)/512)

		for fname in filesOffered:
			peerData = {
				'id': curPeerData['id'],
				'filename': fname, 
				'totalFiles': len(sharedDir),
				'ip': filesOffered[fname]['ip'],
				'port': filesOffered[fname]['port']
			}
			if fname not in sharedDir:
				if DEBUG: print("NEW PEER FILE CREATED!")
				open(fname, '+w').close ## just determined fname's existence so make a newfile w fname
				newDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
									for f in files]
				peerData['filesize'] = os.path.getsize(fname)
				peerData['numchunks'] = int(os.path.getsize(fname)/512)
				peerData['totalFiles'] = len(newDir)
				peerSocket.send(json.dumps(peerData).encode())
			else: 
				chunksProvided = int(filesOffered[fname]['numchunks'])
				chunksAcquired = int(os.path.getsize(fname)/512)
				if chunksAcquired > chunksProvided:
					with open(fname, "+rb") as f:
						f.seek(chunksProvided*512, 0)
						## sending 512KB of data over to the peer
						# print (fname + "======================: " +json.dumps(filesOffered[fname]))
						print(filesOffered)
						print(fname+" connect with: " + str((str(filesOffered[fname]['ip']), int(filesOffered[fname]['port']))))
						upSocket = socket(AF_INET, SOCK_STREAM)
						upSocket.connect((str(filesOffered[fname]['ip']), int(filesOffered[fname]['port']))) ## TCP connection with the new peer
						if DEBUG: print("Upload!!" + " CA = " + str(chunksAcquired) + " CP = " + str(chunksProvided))
						upSocket.send(f.read(524288))

				elif chunksAcquired < chunksProvided:
					
					with open(fname, "+ab") as f:
						# print (fname + "======================: " +json.dumps(filesOffered[fname]))
						print(filesOffered)
						peerConnectSocket, peerAddr = downSocket.accept()
						if DEBUG: print("Download!" + " CA = " + str(chunksAcquired) + " CP = " + str(chunksProvided))
						f.write(peerConnectSocket.recv(524288))
						peerConnectSocket.close()

				else : print(filesOffered)
				if DEBUG: print("NEW SIZE = "+str(os.path.getsize(fname)))
				peerData['filesize'] = os.path.getsize(fname)
				peerData['numchunks'] = int(os.path.getsize(fname)/512)
				peerSocket.send(json.dumps(peerData).encode())



def trackerConnect():
	sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
	                       for f in files] 

	curPeerData['filesize'] = os.path.getsize(sharedDir[0])
	curPeerData['numchunks'] = int(os.path.getsize(sharedDir[0])/512)

	if DEBUG: print("SIZE OF : " + sharedDir[0] + " = " + str(curPeerData['filesize']))
	peerSocket = socket(AF_INET, SOCK_STREAM)
	peerSocket.connect((trackerAddr, trackerPort)) ## TCP connection with the tracker
	## sending it's file info over to the tracker
	countdown = time.time() ## start the timer for to check duration that the peer lives
	initialPeerData = json.dumps({
		"filename": sharedDir[0],
		"filesize": os.path.getsize(sharedDir[0]),
		"totalFiles": len(sharedDir),
		"port": downPort
		})
	peerSocket.send(initialPeerData.encode())

	## waiting to be assigned a new ID
	myId = peerSocket.recv(4).decode()
	curPeerData['id'] = myId
	if DEBUG: print("Current Peer's ID = " + str(myId))
	for file in sharedDir:
		myFiles[sharedDir[0]] = {
			'id': myId,
			'filesize': int(os.path.getsize(file)),
			'numchunks': int(os.path.getsize(file)/512)
		}
	requestThread = threading.Thread(name="REQUEST THREAD", target=requestFiles, args=(peerSocket, countdown))
	requestThread.start()


if __name__ == "__main__":
	connectionThread = threading.Thread(name="TRACKER CONNECT", target=trackerConnect)
	connectionThread.start()