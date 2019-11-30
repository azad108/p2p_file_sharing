import os
from packet.packet import packet
import socket
import sys
import threading
from threading import Timer
import time

if len( sys.argv ) != 5:
  print( "Usage: {} {} {} {} {}".format( 
    sys.argv[ 0 ], "EMULATOR_ADDRESS", "EMULATOR_PORT", "SENDER_PORT", "FILENAME" ) )
  exit( 1 )