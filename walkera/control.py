#import cv2
#import numpy as np
import urllib
import socket
import sys
import struct
import binascii
import time
from threading import Thread
#from Tkinter import *

class Control(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.switch = 0x61
        self.throttle = 0x02bf
        self.rotation = 0x044a
        self.elev = 0x044a
        self.aile =  0x044a
        self.stop = True
        self.cnt = 0
        self.data = bytearray(18)
        self.nudgex = 0
        self.nudgey = 0
        self.nudgez = 0
        self.nudgeyaw = 0
        


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
        
        
        
    def run(self):
        self.threadOn = True
        self.sock = socket.socket()
        self.sock.connect(("192.168.10.1", 2001))

        while self.threadOn:
            #data = update() 
        #key = cv2.waitKey(1)
        #if key ==27:
        #    exit(0)
        #if key == 119:
        #    throttle = (throttle + 10)
            if (self.stop):
                self.throttle = 0x02bf
                self.rotation = 0x044a
                self.elev = 0x044a
                self.aile =  0x044a
                self.cnt = 0
                self.nudgex = 0
                self.nudgey = 0
                self.nudgez = 0
                self.nudgeyaw = 0

            elif (self.cnt > 0):
                if (self.cnt == 1):
                    self.throttle -= self.nudgez
                    self.aile -= self.nudgex
                    self.elev -= self.nudgey
                    self.rotation -= self.nudgeyaw
                    self.nudgex = 0
                    self.nudgey = 0
                    self.nudgez = 0
                    self.nudgeyaw = 0

                self.cnt = self.cnt - 1
                
            self.update()                    
            self.sock.send(self.data) 
            #print binascii.hexlify(data)
            time.sleep(.03)        
            
        
    def stopThread(self):
        self.threadOn = False
    
    def closeSocket(self):
        self.sock.close()
    
    def stopDrone(self):
        self.stop = True
        
    def toggleStop(self):
        self.stop = not self.stop
        print "STOPPED: ", self.stop
        
    def setThrottle(self,val):
        self.throttle = val
        print "set throttle ", (val)
        
    def setAile(self,val):
        self.aile = val
        
    def setElev(self,val):
        self.elev = val
        
    def setRotation(self, val):
        self.rotation = val
        print 'rotation: ', self.rotation
        
    def nudge(self, x, y, z, yaw, cnt = 10):
        self.cnt = self.cnt+cnt
        self.nudgex += x
        self.nudgey += y
        self.nudgez += z
        self.nudgeyaw += yaw
        self.throttle += self.nudgez
        self.aile += self.nudgex
        self.elev += self.nudgey
        self.rotation += self.nudgeyaw