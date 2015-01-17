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

def DrawProcess(velocityq):
    
    while 1:
        data = velocityq.get(True)
#        print "data get:", data
        #g.add_points(data[0],data[1])
        deltax = data[0]
        deltay = data[1]
        roll = data[2]        
        g.add_points(sum(deltax)/len(deltax),sum(deltay)/len(deltay))
        
def VideoProcess(lkq,velq,fdq, ui, vid):
    print 'starting video proc'
    lkProcess = LKProcess(lkq, velq)
    lkProcess.start()
    
    #dp = Process(target=drawProcess, args=(velq,))
    #dp.start()
    
    fdProcess = FaceDetectProcess(fdq)
    fdProcess.start()
    #print 'entering for loop'
    for frame in vid.frames():
        #print 'frame got'
        decode = time.time()
        i = cv2.imdecode(np.fromstring(frame, dtype=np.uint8),1)
        
        #print "decode time:", (time.time()-decode)*1000, "ms"        
        #buffer = manager.Value(ctypes.c_char_p,  cv2.imencode(".bmp", i)[1] )
        #buffer = manager.Value(ctypes.c_char_p, frame) 
        #print "decode and buffer time:", (time.time()-decode)*1000, "ms"
        
        lkq.put(i)
        fdq.put(i)
        
        if ui.recording:
            ui.record(frame)    
        
        #print "decode, buffer and put time:", (time.time()-decode)*1000, "ms"
        #print "new buffer put on queue, lk:", lkq.qsize(), "fd:", fdq.qsize()
        
    print 'exiting video proc'    
if __name__ == '__main__':
    mp.freeze_support()
            
    c = Control()
    v = Video()
      
    try:
        j = Joystick()
        j.attach_control(c)
    except Exception, e:
        print e
        pass

    manager = Manager()
    lkq = manager.Queue()
    velq = manager.Queue()
    fdq = manager.Queue()
    
    ui = Interface(v,c,j)    
    vt = Thread(target=VideoProcess, args=(lkq,velq,fdq,ui,v))
    ui.attach_video_process(vt)
    
    ui.start()
    
    #import graph
    #g = graph.Canvas()
    #g.show()    
    #DrawProcess(velq)