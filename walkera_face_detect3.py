import cv2
import numpy as np
import urllib, base64
import socket
import re
import time

host = "192.168.10.1"
username = "admin"
password = "admin123"
port = 8080

#FUNCTIONS

def sendString(s):
    oculusock.sendall(s+"\r\n")
    print("> "+s)    

def waitForReplySearch(p):
    while True:
        servermsg = (oculusfileIO.readline()).strip()
        print(servermsg)
        if re.search(p, servermsg): 
            break
    return servermsg

#MAIN

#connect
oculusock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
oculusock.connect((host, port))
oculusfileIO = oculusock.makefile() 

#login 
waitForReplySearch("Enter username for MJPG-Streamer at 192.168.10.1:8080:")
sendString(username+":"+password)
waitForReplySearch("Enter password for admin in MJPG-Streamer at 192.168.10.1:8080")

time.sleep(2)
while True:
    sendString("setstreamactivitythreshold 0 10")
    waitForReplySearch("streamactivity: audio")
    sendString("speech please be quiet")
    time.sleep(5)

oculusfileIO.close()
oculusock.close()



# opens the video stream and tracks 
# user:admin, pass:admin123
username = 'admin'
password = 'admin123'

stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''

# face detection classifiers
frontalclassifier = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")     # frontal face pattern detection
profileclassifier = cv2.CascadeClassifier("haarcascade_profileface.xml")      # side face pattern detection
DOWNSCALE = 4

while True:
    bytes+=stream.read(180)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        jpg = bytes[a:b+2]
        bytes= bytes[b+2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
        if frame!= None:
        # if len(jpg) > 1 and ord(jpg[-2]) == 0xff and ord(jpg[-1]) == 0xd9:
            # detect faces and draw bounding boxes
            minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
            miniframe = cv2.resize(frame, minisize)
            frontalfaces = frontalclassifier.detectMultiScale(miniframe)
            profilefaces = profileclassifier.detectMultiScale(miniframe)
            for f in frontalfaces:
                x, y, w, h = [ v*DOWNSCALE for v in f ]
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
            for f in profilefaces:
                x, y, w, h = [ v*DOWNSCALE for v in f ]
                cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0))
            cv2.imshow('authenticated cam',frame)
        if cv2.waitKey(1) ==27:
            exit(0)   