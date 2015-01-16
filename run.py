from walkera.video import Video
from walkera.control import Control
import time
v = Video()
c = Control()

#v.setClassifier("haarcascade_frontalface_alt2.xml")
c.startThread()
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
        
v.startThread()
from inputs.joystick import Joystick
from threading import Thread
try:
    j = Joystick()
    #t = Thread(target = control_loop)
    #t.start()
except Exception, e:
    print e
    pass