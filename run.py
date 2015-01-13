from walkera.video import Video
from walkera.control import Control
v = Video()
c = Control()

v.setClassifier("haarcascade_frontalface_alt2.xml")
v.startThread()
c.startThread()
v.detectFaces = True

Upkey = 2490368
DownKey = 2621440
LeftKey = 2424832
RightKey = 2555904
Space = 32
Enter = 13
Delete = 3014656

def kp(key):
    print "keypress: ", key
    
    
    if key == Enter:
        c.nudge(0,0,0x0111,0)
    if key==Space:
        c.stopDrone()
v.setKeypress(kp)