import os, re, sys, threading, time
from socket import *
DEBUG = True

if len(sys.argv) != 4:
  print("Usage: {} {} {} {}".format(
    sys.argv[0], "TRACKER_IP", "TRACKER_PORT", "MIN_ALIVE_TIME"))
  exit(1)

trackerAddr = sys.argv[1]
trackerPort = int(sys.argv[2])
minTime = sys.argv[3]

sharedDir = [os.path.join(root, f) for root, _, files in os.walk('../shared/')
                       for f in files] 
curPeerFile = str(sharedDir[0])
curPeerFilesize = os.path.getsize(curPeerFile)

if DEBUG: print("SIZE OF : " + curPeerFile + " = " + str(curPeerFilesize))
peerSocket = socket(AF_INET, SOCK_STREAM)
peerSocket.connect((trackerAddr, trackerPort)) ## TCP connection with the tracker 
peerSocket.send(bytes(str(curPeerFilesize).encode())) 

## waiting to be assigned a new ID
myId = peerSocket.recv(4).decode()

if DEBUG: print("Current Peer's ID = " + str(myId))