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

def drawProcess(velocityq):
    
    while 1:
        data = velocityq.get(True)
#        print "data get:", data
        #g.add_points(data[0],data[1])
        deltax = data[0]
        deltay = data[1]
        roll = data[2]        
        g.add_points(sum(deltax)/len(deltax),sum(deltay)/len(deltay))
        
def VideoProcess(lkq,velq,fdq):
    print "Spawning video"
    v = Video()
    
    
    print "Video spawned"
    
    lkProcess = LKProcess(lkq, velq)
    lkProcess.start()
    
    #dp = Process(target=drawProcess, args=(velq,))
    #dp.start()
    
    fdProcess = FaceDetectProcess(fdq)
    fdProcess.start()
    
    ui = Interface()
    ui.startThread()
    
    for frame in v.frames():
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
        
        
if __name__ == '__main__':
    mp.freeze_support()
            
    c = Control()
    c.startThread()
    #v.setClassifier("haarcascade_frontalface_alt2.xml")
    #v.detectFaces = True
    
    

    Upkey = 2490368
    DownKey = 2621440
    LeftKey = 2424832
    RightKey = 2555904
    Space = 32
    Enter = 13
    Delete = 3014656
    PlusKey = 43
    MinusKey = 45
    EscKey = 27
    def kp(key):
        print "keypress: ", key
        
        
        if key == Enter:
            c.nudge(0,0,0x0111,0)
        elif key == Upkey:
            c.nudge(0,0x0111,0,0)
        elif key == DownKey:
            c.nudge(0,-0x0111,0,0)
        elif key == LeftKey:
            c.nudge(-0x0111,0,0,0)
        elif key == RightKey:
            c.nudge(0x0111,0,0,0)
        elif key == PlusKey:
            c.throttle += 10
        elif key == MinusKey:
            c.throttle -= 10
            
        elif key==Space:
            c.toggleStop()
        elif key==113: #q
            c.nudge(0,0,0,-0x0111)
        elif key==119: #w
            c.nudge(0,0,0,0x0111)
        elif key==EscKey:
            c.stopDrone()
            time.sleep(.1)
            c.stopThread()
    #v.setKeypress(kp)



    def control_loop():
        while 1:
            cntrlrdata = j.get()
            
            if (cntrlrdata[4] == 1):
                
                c.stop = False
            if (cntrlrdata[5] == 1):
                
                c.stop = True
            
            #print "Axis 0", cntrlrdata[0], "Axis 1", cntrlrdata[1], "Axis 2", cntrlrdata[2], "Axis 3", cntrlrdata[3]
            if (not c.stop):
                c.setThrottle(int((1 - cntrlrdata[1])*((0x05dc-0x02bf)>>1)) + 0x02bf) #Throttle Range 02bf to 05dc
                c.setRotation(int((1 - cntrlrdata[0])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
                c.setElev(int((1 - cntrlrdata[3])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
                c.setAile(int((1 - cntrlrdata[2])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
            else:
                print cntrlrdata
            #ranging from -1 to 1
            
    try:
        j = Joystick()
        #t = Thread(target = control_loop)
        #t.start()
    except Exception, e:
        print e
        pass
        
    manager = Manager()
    lkq = manager.Queue()
    velq = manager.Queue()
    fdq = manager.Queue()
    vt = Thread(target=VideoProcess, args=(lkq,velq,fdq,))
    vt.start()
    
    import graph
    g = graph.Canvas()
    g.show()
    
    drawProcess(velq)