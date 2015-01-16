from common import anorm2, draw_str
import cv2
import time
import numpy as np
from multiprocessing import Process


class FaceDetectProcess(Process):
    def __init__(self, bufferqueue):
        Process.__init__(self)
        self.bufferqueue = bufferqueue
        self.running = True
        self.DOWNSCALE = 4
    def run(self):
        self.frontalclassifier = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")

        while self.running:
            #print "blocking until we get a buffer"
            i = self.bufferqueue.get(True) #block until new raw_frame
            #print "buffer got"
            startd = time.time()
        
            #i= cv2.imdecode(np.fromstring(raw_frame.value, dtype=np.uint8),1)
            start = time.time()
        

            minisize = (i.shape[1]/self.DOWNSCALE,i.shape[0]/self.DOWNSCALE)
            miniframe = cv2.resize(i, minisize)
            frontalfaces = self.frontalclassifier.detectMultiScale(miniframe)
            for f in frontalfaces:
                x, y, w, h = [ v*self.DOWNSCALE for v in f ]
            #     # draws bounding box
                cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
            if len(frontalfaces) >= 1:
                x, y, w, h = [ v*self.DOWNSCALE for v in frontalfaces[0] ]
                if i.shape[1]*(2/3.) < x+w/2:# too far right
                    cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
            #         # print "turn counterclockwise"
                elif i.shape[1]*(1/3.) > x+w/2: # too far left
            #         # print "turn clockwise"
                    cv2.rectangle(i, (x,y), (x+w,y+h), (0,255,0))
                else: # centered
            #         # print "centered"
                    cv2.rectangle(i, (x,y), (x+w,y+h), (255,0,0))
            #     print (x+w/2.),(y+h/2.),(w**2+h**2)**0.5
            end = time.time()
            print 'fd latency', (end-start)*1000, 'ms', (end-startd)*1000, 'ms'
            
            cv2.imshow('face_detect', i)
            key = cv2.waitKey(1)
            