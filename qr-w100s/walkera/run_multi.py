from walkera.video import Video
from walkera.control import Control
from multiprocessing import Queue, Process, Array, Manager
import multiprocessing as mp
import ctypes
import time

from inputs.joystick import Joystick
from threading import Thread

from vision.lk import LKProcess
from vision.facedetect import FaceDetectProcess
import cv2
import numpy as np
from interface import Interface
import os

def DrawProcess(velocityq):
    
    while 1:
        data = velocityq.get(True)
#        print "data get:", data
        #g.add_points(data[0],data[1])
        deltax = data[0]
        deltay = data[1]
        roll = data[2]        
        g.add_points(sum(deltax)/len(deltax),sum(deltay)/len(deltay))

class VideoProcess(Thread):        
    def __init__(self, manager, ui, vid):
        Thread.__init__(self)
        self.vid = vid
        self.ui = ui
        self.manager = manager
        print 'starting video proc'
        self.lkq = self.manager.Queue()
        self.velq = self.manager.Queue()
        self.fdq = self.manager.Queue()
        self.lkProcess = LKProcess(self.lkq, self.velq)
        
        #dp = Process(target=drawProcess, args=(velq,))
        #dp.start()
        
        self.fdProcess = FaceDetectProcess(self.fdq)
    def set_video_src(self,vid):
        self.vid = vid
        
    def run(self):    
        self.lkProcess.start()
        self.fdProcess.start()
        #print 'entering for loop'
        for frame in self.vid.frames():
            #print 'frame got'
            decode = time.time()
            i = cv2.imdecode(np.fromstring(frame, dtype=np.uint8),1)
            
            #print "decode time:", (time.time()-decode)*1000, "ms"        
            #buffer = manager.Value(ctypes.c_char_p,  cv2.imencode(".bmp", i)[1] )
            #buffer = manager.Value(ctypes.c_char_p, frame) 
            #print "decode and buffer time:", (time.time()-decode)*1000, "ms"
            
          
            #print "lkq:", self.lkq.qsize()
            if (self.lkq.qsize()<3):
                self.lkq.put(i)
                self.fdq.put(i)
            
            if self.ui.recording:
                self.ui.record(i)    
            
            #print "decode, buffer and put time:", (time.time()-decode)*1000, "ms"
            #print "new buffer put on queue, lk:", lkq.qsize(), "fd:", fdq.qsize()
            
        print 'exiting video proc'    
        
if __name__ == '__main__':
    mp.freeze_support()
            
            
           
    c = Control()
    v = Video()
    j = None  
    try:
        j = Joystick()
        j.attach_control(c)
    except Exception, e:
        print e
        pass

    manager = Manager()

    
    ui = Interface(v,c,j)    
    vp = VideoProcess(manager,ui,v)
    ui.attach_video_process(vp)
    
    ui.start()
    
    #import graph
    #g = graph.Canvas()
    #g.show()    
    #DrawProcess(velq)