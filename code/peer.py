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


	upSocket = socket(AF_INET, SOCK_STREAM) # create a TCP socket that waits for a new peer to connect
	upSocket.bind(('', 0))
	upSocket.listen(80)
	upPort = upSocket.getsockname()[1] 
	filesLock = threading.Lock()
	writeLocks = {}

def uploadFiles(myId):
	while True:
		print("ACCEPTINGGGGG AT ")
		peerConnectSocket, peerAddr = upSocket.accept()
		print("ACCEPTED!!")
		request = peerConnectSocket.recv(128)
		if (request == 0):
			peerConnectSocket.close()
			continue
		request = json.loads(request)
		print("RECEIVED!!")
		with open(request['filename'], "+rb") as f:
			f.seek(request['startByte'], 0)
			start = request['startByte']
			while start < request['originalSize']:
				## sending 512KB of data over to the peer
				peerConnectSocket.send(f.read(524288))
				start+=524288


def download(file, peers, originalSize, acquiredSize, startByte, endByte):
	print("OG SIZE = " + str(originalSize)+ " CUR SIZE = " + str(os.path.getsize(file)))
	if os.path.getsize(file) == originalSize: os._exit(0)
	with writeLocks[file]:
		print("DOWNLOADING "+ file)
		myPeer = peers[0]
		print (peers)
		print (myPeer)
		downSocket = socket(AF_INET, SOCK_STREAM)
		downSocket.connect((str(myPeer['ip']), myPeer['port']))
		print(myPeer)
		with open(file, "+ab") as f: 
			start = 0
			fileRequest = {
				'filename': file,
				'startByte': startByte,
				'endByte': endByte,
				'originalSize': originalSize
			}
			downSocket.send(json.dumps(fileRequest).encode())
			start = startByte
			while start < originalSize:
				## sending 512KB of data over to the peer
				f.write(downSocket.recv(524288))
				start+=524288
			downSocket.close()

def requestFiles(myId, hostIP, peerSocket, startTime):
	global trackerAddr, trackerPort, minAliveTime, upSocket, downSocket, upPort
	
	while True:
		trackerData = peerSocket.recv(1024).decode()
		trackerData = json.loads(trackerData)
		peerId = trackerData['id']
		curFilename = trackerData['filename']
		peers = trackerData['peers']
		allFiles[curFilename] = peers

		for peer in peers:
			originalSize = peers[peer]['originalSize']
			if peer not in allPeers and peer != str(myId): allPeers.append(peer)
		sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
		                       for f in files] 
		if curFilename not in sharedDir:
			open(curFilename, '+w').close ## just determined fname's existence so make a newfile w fname
			if DEBUG: print(curFilename+" CREATED!")
			writeLocks[curFilename] = threading.Lock()	
		allFiles[curFilename][str(myId)]={
				'ip': hostIP,
				'port': upPort,
				'originalSize': originalSize,
				'acquiredSize': os.path.getsize(curFilename)
			} 

		sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
		                       for f in files] 

		acquiredSize = os.path.getsize(curFilename)
		if acquiredSize < originalSize:
			downloadPeers = []
			for peer in peers:
				if peers[peer]['acquiredSize'] > acquiredSize and peer != str(myId): 
					downloadPeers.append(peers[peer])

			# downloadPeers.sort(key=lambda p: p['acquiredSize'], reverse=True)
			if len(downloadPeers) >= 1:
			# 	maxSize = downloadPeers[len(downloadPeers)-1]['acquiredSize']
			# 	median = acquiredSize + (maxSize - acquiredSize)
			# 	firstPeers = filter(lambda p: p['acquiredSize'] <= median, downloadPeers)
			# 	lastPeers = filter(lambda p: p['acquiredSize'] > median, downloadPeers)
			# 	if len(firstPeers) >= 1 and len(lastPeers) >= 1:
			# 		firstDownloadThread = threading.Thread(name="FIRST PART DOWNLOAD THREAD", target=download,\
			# 			args=(firstPeers, originalSize, acquiredSize, acquiredSize, median))
			# 		lastDownloadThread = threading.Thread(name="LAST PART DOWNLOAD THREAD", target=download,\
			# 			args=(lastPeers, originalSize, acquiredSize, median+1, originalSize))
			# 		firstDownloadThread.start()
			# 		lastDownloadThread.start()
			# else:
				downloadThread = threading.Thread(name="DOWNLOAD THREAD", target=download,\
					args=(curFilename, downloadPeers, originalSize, acquiredSize, acquiredSize, originalSize))
				downloadThread.start()

		## update acquired size since it's downloaded curFile
		allFiles[curFilename][str(myId)] = {
				'ip': hostIP,
				'port': upPort,
				'originalSize': originalSize,
				'acquiredSize': os.path.getsize(curFilename)
			}

		isDownloaded = True
		isClosed = 0
		for file in allFiles:
			if allFiles[file][str(myId)]['originalSize'] > allFiles[file][str(myId)]['acquiredSize']:
				isDownloaded = False

		if isDownloaded and time.time()-startTime >= float(minAliveTime): 
			print("TIME TAKEN: " + str(time.time()-startTime))
			isClosed = 1
			
		response = {
			'id': myId,
			'filename': curFilename,
			'peers': allFiles[curFilename],
			'isClosed': isClosed
		} 
		peerSocket.send(json.dumps(response).encode()) 
		if isClosed == 1:
			peerSocket.close()
			os._exit(0)

		



def trackerConnect():
	global hostIP, upPort
	sharedDir = [os.path.join(root, f) for root, _, files in os.walk('shared/')
	                       for f in files]

	curPeerData['filesize'] = os.path.getsize(sharedDir[0])
	curPeerData['numchunks'] = math.ceil(os.path.getsize(sharedDir[0])/512)
	
	if DEBUG: print("SIZE OF : " + sharedDir[0] + " = " + str(curPeerData['filesize']))
	peerSocket = socket(AF_INET, SOCK_STREAM)
	peerSocket.connect((trackerAddr, trackerPort)) ## TCP connection with the tracker
	## sending it's file info over to the tracker
	startTime = time.time() ## start the timer for to check duration that the peer lives
	initialPeerData = json.dumps({
		"filename": sharedDir[0],
		"filesize": os.path.getsize(sharedDir[0]),
		"totalFiles": len(sharedDir),
		"port": upPort 
	})
	peerSocket.send(initialPeerData.encode())

	## waiting to be assigned a new ID
	ackData = json.loads(peerSocket.recv(512).decode())
	myId = ackData['id']
	myIP = ackData['ip']
	curPeerData['id'] = myId
	if DEBUG: print("Current Peer's ID = " + str(myId))
	requestThread = threading.Thread(name="REQUEST THREAD", target=requestFiles, args=(myId, myIP, peerSocket, startTime))
	requestThread.start()
	uploadThread = threading.Thread(name="UPLOAD THREAD", target=uploadFiles, args=(myId,))
	uploadThread.start()


if __name__ == "__main__":
	connectionThread = threading.Thread(name="TRACKER CONNECT", target=trackerConnect)
	connectionThread.start()