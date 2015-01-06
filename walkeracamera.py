import cv2
import numpy as np
import urllib
import socket

stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''
MJPEGBuffer=''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect( ( '192.168.10.1', 8080 ) )
sock.send( "GET /index.htm HTTP/1.1\r\nUser-Agent: Walkera Remote\r\n\r\n")

# print stream.read(12536)
while True:
    data=stream.read(1552)
    # data = sock.recv(1552)
    # print data
    # b = bytes.find('--markmarkmark')
    # print bytes

    if str(data).startswith('\r\n--donotcross'):
        MJPEGBuffer = ''
        if len(data) > 0x2c:
            MJPEGBuffer += str(bytearray(data[0x2c:]))
    else:
        if data.startswith('HTTP'):
            if len(data) > 146: # That's the fixed size of the HTTP reply header
                MJPEGBuffer += str(bytearray(data[146:]))
        else:
            MJPEGBuffer += str(bytearray(data))
        if len(MJPEGBuffer) > 1 and ord(MJPEGBuffer[-2]) == 0xff and ord(MJPEGBuffer[-1]) == 0xd9:
            stream=cv2.imdecode(np.fromstring(MJPEGBuffer, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
            cv2.imshow("Camera Wifi", stream)
            # if frame!= None:
                # cv2.imshow('authenticated cam',frame)
            if cv2.waitKey(1) ==27:
                exit(0) 

    # a = bytes.find('\xff\xd8')
    # b = bytes.find('\xff\xd9')
    # if a!=-1 and b!=-1:
    #     jpg = bytes[a:b+2]
    #     bytes= bytes[b+2:]
    #     frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
