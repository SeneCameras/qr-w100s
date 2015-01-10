#import cv2
#import numpy as np
import urllib
import socket
import sys
import struct
import binascii
import time
import threading
#from Tkinter import *

# opens the video stream
#stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''

# 
switch = 0x51
throttle = 0x01
rotation = 0x7f
elev = 0x7f
aile =  0x7f

off = [ 0x60, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
off.append( (sum(off)) & 0xff )
off=struct.pack("18B",*tuple(off))

threadOn = True
data = bytearray(18)

sock = socket.socket()
sock.connect(("192.168.10.1", 2001))

def update():
    # data[0] = 0x61
    d = bytearray(18)
    d[0] = switch
    d[1] = throttle >> 8
    d[2] = throttle
    d[3] = rotation >> 8
    d[4] = rotation
    d[5] = elev >> 8
    d[6] = elev
    d[7] = aile >> 8
    d[8] = aile
    d[9] = aile >> 8
    d[10] = aile
    d[11] = throttle >> 8
    d[12] = throttle
    d[13] = rotation >> 8
    d[14] = rotation
    d[15] = elev >> 8
    d[16] = elev
    d[17] = sum(d[0:17]) & 0xFF
    return d

def loop():
    while threadOn:
        #data = update() 
    #key = cv2.waitKey(1)
    #if key ==27:
    #    exit(0)
    #if key == 119:
    #    throttle = (throttle + 10)

        sock.send(data) 
        #print binascii.hexlify(data)
        time.sleep(.03)
    sock.close()
    # sock.send(data)

    #bytes+=stream.read(1080)
    #a = bytes.find('\xff\xd8')
    #b = bytes.find('\xff\xd9')
    #if a!=-1 and b!=-1:
    #    jpg = bytes[a:b+2]
    #    bytes= bytes[b+2:]
        #frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
        #if frame!= None:
		#	cv2.imshow('authenticated cam',frame)
        #key = cv2.waitKey(1)

    	#if key ==27:
    	#    exit(0)
        # if key == 119:
        #     sock.send(off)
            # throttle = (throttle + 10) & 0xFF
        #if key == 115 and throttle > 1:
        #    sock.send(data)
            # throttle -= 10

        #root.after(25) 

#root.mainloop()
t = threading.Thread(target=loop)

#sock.send(off)
#sock.close()
