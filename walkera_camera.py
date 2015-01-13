import cv2
import numpy as np
import urllib
import socket
import httplib
import urllib2
import base64
# import re

# opens the video stream of the qr w100s after given the user and pass
username = "admin"
password = "admin123"
# stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''
MJPEGBuffer=''
# sock = socket.socket()

request = urllib2.Request("http://192.168.10.1:8080/?action=stream")
print request
base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
request.add_header("Authorization", "Basic %s" % base64string)   
result = urllib2.urlopen(request)
print result

# HTTPConnection = httplib.HTTPConnection('http://192.168.10.1:8080/?action=stream')
conn = httplib.HTTPConnection('192.168.10.1',8080)
# print HTTPConnection.getresponse()
conn.request("GET", "/index.html")
r1 = conn.getresponse()
print r1.status, r1.reason
conn.connect()
conn.request()
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.settimeout(5)
# sock.connect( ( '192.168.10.1', 8080 ) )



while True:
    # data=stream.read(1552)
    data = sock.recv(1552)
    print data

    if str(data).startswith('\r\n--markmarkmark'):
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
