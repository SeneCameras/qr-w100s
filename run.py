from walkera.video import Video
v = Video()
v.setClassifier("haarcascade_frontalface_alt2.xml")
v.startThread()
v.detectFaces = True
def kp(key):
    print "keypress: ", key
v.setKeypress(kp)