import cv2
import numpy as np
import urllib
import socket
import sys
import struct
# import binascii
import time
import threading
#from Tkinter import *

class Walkera:
    def __init__(self):
        self.switch = 0x61
        self.throttle = 0x02bf
        self.rotation = 0x044a
        self.elev = 0x044a
        self.aile =  0x044a

        self.stream=urllib.urlopen('http://admin:admin123@192.168.10.1:8080/?action=stream')
    
        self.data = bytearray(18)

        self.sock = socket.socket()
        self.sock.connect(("192.168.10.1", 2001))

    def update(self):
        # data[0] = 0x61
        self.data[0] = self.switch
        self.data[1] = self.throttle >> 8
        self.data[2] = self.throttle & 0xff
        self.data[3] = self.rotation >> 8
        self.data[4] = self.rotation & 0xff
        self.data[5] = self.elev >> 8
        self.data[6] = self.elev & 0xff
        self.data[7] = self.aile >> 8
        self.data[8] = self.aile & 0xff
        self.data[9] = self.aile >> 8
        self.data[10] = self.aile & 0xff
        self.data[11] = self.throttle >> 8
        self.data[12] = self.throttle & 0xff
        self.data[13] = self.rotation >> 8
        self.data[14] = self.rotation & 0xff
        self.data[15] = self.elev >> 8
        self.data[16] = self.elev & 0xff
        self.data[17] = sum(self.data[0:17]) & 0xFF
        
    def loop(self):
        self.threadOn = True
        while self.threadOn:
            self.update()
            self.sock.send(self.data) 
            bytes+=self.stream.read(1080)
            a = bytes.find('\xff\xd8')
            b = bytes.find('\xff\xd9')
            if a!=-1 and b!=-1:
                jpg = bytes[a:b+2]
                bytes= bytes[b+2:]
                frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
                if frame!= None:
                    # detect faces
                    minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
                    miniframe = cv2.resize(frame, minisize)
                    frontalfaces = frontalclassifier.detectMultiScale(miniframe)
                    for f in frontalfaces:
                        x, y, w, h = [ v*DOWNSCALE for v in f ]
                        # draws bounding box
                        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
                    if len(frontalfaces) >= 1:
                        x, y, w, h = [ v*DOWNSCALE for v in frontalfaces[0] ]
                        if frame.shape[1]*(2/3.) < x+w/2:# too far right
                            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
                            print "turn counterclockwise"
                        elif frame.shape[1]*(1/3.) > x+w/2: # too far left
                            print "turn clockwise"
                            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0))
                        else: # centered
                            print "centered"
                            cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0))
                    cv2.imshow('authenticated cam',frame)
                    key = cv2.waitKey(1)
                    if key ==27: # 'esc' key
                        w.threadOn = 0
                    if key == 119: # 'w' key
                        throttle = (throttle + 10) & 0xFF
                    if key == 115 and throttle > 1: # 's' key
                        throttle -= 10
            time.sleep(.03)
        self.sock.close()
   

w = Walkera()
t = threading.Thread(target=w.loop)
t.start()
#then try modifying w.throttle to 0x03ba or something 


#to stop it: 
# w.threadOn = 0