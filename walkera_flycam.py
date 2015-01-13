import cv2
import numpy as np
import urllib
import socket
import sys
import struct
import binascii
from Tkinter import *

host = "192.168.10.1"
port = 2001

# opens the video stream
stream=urllib.urlopen('http://admin:admin123@192.168.10.1:8080/?action=stream')

bytes=''
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
sock.connect( ( host, 8080 ) )
# print sock.recv(1080)


control_off = 0x60
control_on = 0x61
throttle = 0x01             # off:0x01, half:0x79, full:0xff
rotation = 0x7f             # center:0x7f, ?right:0xff, left:0x01
elev = 0x7f                 # center:0x7f, ?right:0xff, left:0x01
aile =  0x7f                # center:0x7f, ?right:0xff, left:0x01
rudder = 0x7f
gyro = 0x01
byte9 = 0x00
bytea = 0x00

# the off message for the drone
off = [ 0x60, 0x00, throttle, 0x00, rotation, 0x00, elev, 0x00, aile,
        0x00, aile, 0x00, throttle, 0x00, rotation, 0x00, elev]
off.append( (sum(off)) & 0xff )
off=struct.pack("18B",*tuple(off))

sock = socket.socket()
sock.connect((host, port))
data = bytearray(12)

def update(data):
    payload = [ 0xaa, 0x55, 0x61, throttle, rudder, elev, aile, gyro, throttle, byte9, bytea]
    payload.append( (sum(payload)) & 0xff )
    payload=struct.pack("12B",*tuple(payload))
    return payload

    # data[0] = wireless_control
    # data[1] = throttle >> 8
    # data[2] = throttle
    # data[3] = rotation >> 8
    # data[4] = rotation
    # data[5] = elev >> 8
    # data[6] = elev
    # data[7] = aile >> 8
    # data[8] = aile
    # data[9] = aile >> 8
    # data[10] = aile
    # data[11] = throttle >> 8
    # data[12] = throttle
    # data[13] = rotation >> 8
    # data[14] = rotation
    # data[15] = elev >> 8
    # data[16] = elev
    # data[17] = sum(data[0:17]) & 0xFF
    # return data


# turn on
# wireless_control = control_on

while True:
    data = update(data)

    # attempt to control drone 
    # key = cv2.waitKey(1)
    # if key ==27: # 'esc' key
    #     exit(0)
    # if key == 119: # 'w' key
    #     throttle = (throttle + 1)

    sock.send(data)
    # controls mesage
    print binascii.hexlify(data)

    bytes+=stream.read(1080)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        jpg = bytes[a:b+2]
        bytes= bytes[b+2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
        if frame!= None:
			cv2.imshow('authenticated cam',frame)
        key = cv2.waitKey(1)

    	if key ==27: # 'esc' key
    	    exit(0)
        if key == 119: # 'w' key
        #     sock.send(off)
            throttle = (throttle + 10) & 0xFF
        if key == 115 and throttle > 1: # 's' key
            # sock.send(data)
            throttle -= 10

sock.send(off)
sock.close()
