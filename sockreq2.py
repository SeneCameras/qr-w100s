import urllib2
import time
import cv2
import numpy as np

def readframes(resp, recv_buffer=4096, delim='\n'):
    buffer = ''
    global jpgs
    jpgs = 0
    data = True
    global fulldata
    fulldata = ''
    state = 0
    ts = 0
    print ' in readframes'
    while data:
        data = resp.read(recv_buffer)
        # print data
        fulldata += data
        buffer += data

        while buffer.find(delim) != -1:
            line, buffer = buffer.split("\n", 1)
            if state==0:
                if line[0:20] == "--boundarydonotcross":
                    state = 1
            elif state==1:
                #print line.split(":")
                state = 2
            elif state==2:
                #print line
                datalength = int(line.split(":")[1][1:-1])
                state = 3
                #print "datalen", datalength
                #print buffer
            elif state==3:
                state = 4
                
                timestamp = float(line.split(":")[1][1:-1])
                # print "timestamp:", timestamp
                #print "lag", timestamp - ts, 1/( timestamp - ts)
                # ts = timestamp
            else:
                while(len(buffer) < datalength):
                    bytes_remaining = datalength - len(buffer)
                    data = resp.read(bytes_remaining)
                    fulldata += data
                    buffer += data
                state = 0
                yield buffer
    return

if __name__ == "__main__":

    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

    top_level_url = "http://192.168.10.1:8080"
    password_mgr.add_password(None, top_level_url, 'admin', 'admin123')

    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    opener.open("http://192.168.10.1:8080/?action=stream")
    urllib2.install_opener(opener)
    print 'opening url'
    # resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")
    resp = open('noFaceRecognized.avi','r')
    # size = 0
    DOWNSCALE = 4
    frontalclassifier = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")
    a = time.time()
    n = 1
    avg = 0
    x = 0
    # moviefile = open('facePeriodicallyRecognized.avi','w')

    for frame in readframes(resp):
        # x = x+1
        # t = time.time()
        # fps = 1/(t-a)
        # print "FPS: ", fps
        # a = t
        try:
            frame = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
            # if frame != None:
            # jpgs += 1
            if True:
                # detect faces
                minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
                miniframe = cv2.resize(frame, minisize)
                frontalfaces = frontalclassifier.detectMultiScale(miniframe)
                for f in frontalfaces:
                    x, y, w, h = [ v*DOWNSCALE for v in f ]
                #     # draws bounding box
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
                if len(frontalfaces) >= 1:
                    x, y, w, h = [ v*DOWNSCALE for v in frontalfaces[0] ]
                    if frame.shape[1]*(2/3.) < x+w/2:# too far right
                        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
                #         # print "turn counterclockwise"
                    elif frame.shape[1]*(1/3.) > x+w/2: # too far left
                #         # print "turn clockwise"
                        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0))
                    else: # centered
                #         # print "centered"
                        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0))
                #     print (x+w/2.),(y+h/2.),(w**2+h**2)**0.5

                cv2.imshow('i',frame)
                if cv2.waitKey(1) ==27:
                    # moviefile.write(fulldata)
                    # print fulldata

                    exit(0)
        except Exception, e:
            print e

print jpgs