import os, re, sys, threading, time, json, math, socket
from socket import *
DEBUG = True

if __name__ == "__main__":
	if len(sys.argv) != 4:
	  print("Usage: {} {} {} {}".format(
	    "./peer", "TRACKER_IP", "TRACKER_PORT", "MIN_ALIVE_TIME"))
	  exit(1)
	allFiles = {} ## Dictionary containing all the files that the current 
				 ## peer has in its shared directory
				 ## mapped to their containing peers
	allPeers = [] ## list of all currently active peer's IDs apart from current
	curPeerData = {}
	trackerAddr = sys.argv[1]
	trackerPort = int(sys.argv[2])
	minAliveTime= sys.argv[3]


	downSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	downSocket.bind(('', 0))
	downSocket.listen(8)
	downPort = downSocket.getsockname()[1] 
	filesLock = threading.Lock()

def uploadFiles(myId):
	
	with open("fname", "+rb") as f:
		f.seek(chunksProvided*512, 0)
		## sending 512KB of data over to the peer
		# print (fname + "======================: " +json.dumps(filesOffered[fname]))
		print(filesOffered)

		print(fname+" connect with: " + str((str(filesOffered[fname]['ip']), int(filesOffered[fname]['port']))))
		upSocket = socket(AF_INET, SOCK_STREAM)
		upSocket.connect((str(filesOffered[fname]['ip']), int(filesOffered[fname]['port']))) ## TCP connection with the new peer
		upSocket.send(f.read(524288))

	for file in allFiles
def requestFiles(myId, hostIP, peerSocket, countdown):
	global trackerAddr, trackerPort, minAliveTime, upSocket, downSocket, downPort
	timedOut = time.time()-countdown >= float(minAliveTime)
	recvdAll = False
	while True:
		if recvdAll: break

		trackerData = peerSocket.recv(1024).decode()
		trackerData = json.loads(trackerData)
		peerId = trackerData['id']
		curFilename = trackerData['filename']
		peers = trackerData['peers']
		
		for peer in peers: 
			originalSize = peers[peer]['originalSize']
			if peer not in allPeers and peer != str(myId): allPeers.append(peer)
		sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
		                       for f in files] 
		if curFilename not in sharedDir:
			open(curFilename, '+w').close ## just determined fname's existence so make a newfile w fname
			if DEBUG: print(curFilename+" CREATED!")
		allFiles[curFilename]= {
		str(myId):{
				'ip': hostIP, 
				'port': downPort,
				'originalSize': originalSize,
				'acquiredSize': os.path.getsize(curFilename)
			}
		}

		sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
		                       for f in files] 

		acquiredSize = os.path.getsize(curFilename)
		if acquiredSize < originalSize:
			with open(curFilename, "+ab") as f: 
				peerConnectSocket, peerAddr = downSocket.accept()
				f.write(peerConnectSocket.recv(4194304))
				peerConnectSocket.close()

		allFiles[curFilename][str(myId)]['acquiredSize']= os.path.getsize(curFilename)
		response = {
			'id': myId,
			'filename': curFilename,
			'peers': allFiles[curFilename]
		}


		print(allFiles)
		peerSocket.send(json.dumps(response).encode())
			# peerData = {
			# 	'id': curPeerData['id'],
			# 	'filename': fname, 
			# 	'totalFiles': len(sharedDir),
			# 	'ip': filesOffered[fname]['ip'],
			# 	'port': filesOffered[fname]['port']
			# }
			# if fname not in sharedDir:
			# 	newDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
			# 						for f in files]
			# 	peerData['filesize'] = os.path.getsize(fname)
			# 	peerData['numchunks'] = math.ceil(os.path.getsize(fname)/512)
			# 	peerData['totalFiles'] = len(newDir)
			# 	peerSocket.send(json.dumps(peerData).encode())
			# else: 
			# 	if DEBUG: print("PEER FILE EXITS!")
			# 	chunksProvided = int(filesOffered[fname]['numchunks'])
			# 	chunksAcquired = math.ceil(os.path.getsize(fname)/512)
			# 	if DEBUG: 
			# 		print("THIS PEER: " +str()+ fname + " - " + str(chunksAcquired) + " CP = " + str(chunksProvided))

			# if chunksAcquired > chunksProvided:


			# elif chunksAcquired < chunksProvided: 

			
			# if DEBUG: print("NEW SIZE = "+str(os.path.getsize(fname)))
			# peerData['filesize'] = os.path.getsize(fname)
			# peerData['numchunks'] = math.ceil(os.path.getsize(fname)/512)
			


def trackerConnect():
	global hostIP
	sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
	                       for f in files]

	curPeerData['filesize'] = os.path.getsize(sharedDir[0])
	curPeerData['numchunks'] = math.ceil(os.path.getsize(sharedDir[0])/512)

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
	ackData = json.loads(peerSocket.recv(512).decode())
	myId = ackData['id']
	myIP = ackData['ip']
	curPeerData['id'] = myId
	if DEBUG: print("Current Peer's ID = " + str(myId))
	requestThread = threading.Thread(name="REQUEST THREAD", target=requestFiles, args=(myId, myIP, peerSocket, countdown))
	requestThread.start()
	uploadThread = threading.Thread(name="UPLOAD THREAD", target=uploadFiles, args=(myId,))
	uploadThread.start()


if __name__ == "__main__":
	connectionThread = threading.Thread(name="TRACKER CONNECT", target=trackerConnect)
	connectionThread.start()