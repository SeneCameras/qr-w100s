from walkera.video_lk import Video
from walkera.control import Control
import time
v = Video()
c = Control()

v.setClassifier("haarcascade_frontalface_alt2.xml")
v.startThread()
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
v.setKeypress(kp)