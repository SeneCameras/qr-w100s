import cv2
import numpy as np
import urllib2
import socket
import sys
import struct
import binascii
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

        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        top_level_url = "http://192.168.10.1:8080"
        password_mgr.add_password(None, top_level_url, 'admin', 'admin123')

        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        opener.open("http://192.168.10.1:8080/?action=stream")
        urllib2.install_opener(opener)
        print 'opening url'
        self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")

        # self.stream=urllib.urlopen('http://admin:admin123@192.168.10.1:8080/?action=stream')
    
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
        
    def readframes(resp, recv_buffer=4096, delim='\n'):
        buffer = ''
        while data:
            data = resp.read(recv_buffer)
            buffer += data

            while buffer.find(delim) != -1:
                line, buffer = buffer.split("\n", 1)
                if state==0:
                    if line[0:20] == "--boundarydonotcross":
                        state = 1
                elif state==1:
                    print line.split(":")
                    state = 2
                elif state==2:
                    print line
                    datalength = int(line.split(":")[1][1:-1])
                    state = 3
                    print "datalen", datalength
                    #print buffer
                elif state==3:
                    state = 4
                    
                    timestamp = float(line.split(":")[1][1:-1])
                    print "timestamp:", timestamp
                    print "lag", timestamp - ts, 1/( timestamp - ts)
                    ts = timestamp
                else:
                    while(len(buffer) < datalength):
                        bytes_remaining = datalength - len(buffer)
                        data = resp.read(bytes_remaining)
                        buffer += data
                    state = 0
                # bytes+=self.stream.read(1080)
                a = data.find('\xff\xd8')
                b = data.find('\xff\xd9')
                if a!=-1 and b!=-1:
                    jpg = data[a:b+2]
                    data= data[b+2:]
                    self.frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
                yield buffer
        return
        
    def loop(self):
        self.threadOn = True
        while self.threadOn:
            self.update()
            self.sock.send(self.data) 
            self.readframes(self.resp)
            # bytes+=self.stream.read(1080)
            # a = bytes.find('\xff\xd8')
            # b = bytes.find('\xff\xd9')
            # if a!=-1 and b!=-1:
            #     jpg = bytes[a:b+2]
            #     bytes= bytes[b+2:]
            #     frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
            if self.frame!= None:
                cv2.imshow('authenticated cam',self.frame)
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