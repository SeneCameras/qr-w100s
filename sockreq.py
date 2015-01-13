import urllib2
import time
import cv2
import numpy as np

def readframes(resp, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True
    state = 0
    ts = 0
    print ' in readframes'
    while data:
        data = resp.read(recv_buffer)
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
                #print "timestamp:", timestamp
                #print "lag", timestamp - ts, 1/( timestamp - ts)
                ts = timestamp
            else:
                while(len(buffer) < datalength):
                    bytes_remaining = datalength - len(buffer)
                    data = resp.read(bytes_remaining)
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
    resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")
    #print resp.read(10)
    size = 0
    a = time.time()
    n = 1
    avg = 0
    x = 0

    for frame in readframes(resp):
      
        #dump = open('dump/dumpframe'+str(x),'w')
        x = x+1
        #dump.write(frame)
        t = time.time()
        fps = 1/(t-a)
        #print "frame len: ", len(frame)
        print "FPS: ", fps
        a = t

        #a = frame.find('\xff\xd8')
        #b = frame[-20:].find('\xff\xd9')
        #if b != -1:
        #    frame = frame[0:-20+b]
        #print a, b
        try:
            i = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
            cv2.imshow('i',i)
            if cv2.waitKey(1) ==27:
                exit(0)
        except Exception, e:
            print e   
        #if b==-1:
        #    print "HAS -1 b", x
        #if a!=-1 and b!=-1:
        #    jpg = frame[a:b+2]
        #    bytes= frame[b+2:]
        
        #x = x+1
        #if (x==120):           
        #    x = 0
        #    print frame
 

