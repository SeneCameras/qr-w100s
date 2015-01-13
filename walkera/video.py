import urllib2
import time
import cv2
import numpy as np
import threading
class Video:
    def __init__(self):
        self.onkeypress = False
        self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        self.top_level_url = "http://192.168.10.1:8080"
        self.password_mgr.add_password(None, self.top_level_url, 'admin', 'admin123')

        self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
        self.opener = urllib2.build_opener(self.handler)
        self.opener.open("http://192.168.10.1:8080/?action=stream")
        urllib2.install_opener(self.opener)
        print 'opening url'
        
        
    def readframes(self, recv_buffer=4096, delim='\n'):
        buffer = ''
        data = True
        self.state = 0
        ts = 0
        print ' in readframes'
        while data:
            data = self.resp.read(recv_buffer)
            buffer += data

            while buffer.find(delim) != -1:
                line, buffer = buffer.split("\n", 1)
                if self.state==0:
                    if line[0:20] == "--boundarydonotcross":
                        self.state = 1
                elif self.state==1:
                    #print line.split(":")
                    self.state = 2
                elif self.state==2:
                    #print line
                    datalength = int(line.split(":")[1][1:-1])
                    self.state = 3
                    #print "datalen", datalength
                    #print buffer
                elif self.state==3:
                    self.state = 4
                    
                    timestamp = float(line.split(":")[1][1:-1])
                    #print "timestamp:", timestamp
                    #print "lag", timestamp - ts, 1/( timestamp - ts)
                    ts = timestamp
                else:
                    while(len(buffer) < datalength):
                        bytes_remaining = datalength - len(buffer)
                        data = self.resp.read(bytes_remaining)
                        buffer += data
                    self.state = 0
                    yield buffer
        return


    def loop(self):
        self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")
        #print resp.read(10)
        size = 0
        a = time.time()
        n = 1
        avg = 0
        x = 0

        for frame in self.readframes():
          
            #dump = open('dump/dumpframe'+str(x),'w')
            x = x+1
            #dump.write(frame)
            t = time.time()
            fps = 1/(t-a)
            #print "frame len: ", len(frame)
            #print "FPS: ", fps
            a = t

            #a = frame.find('\xff\xd8')
            #b = frame[-20:].find('\xff\xd9')
            #if b != -1:
            #    frame = frame[0:-20+b]
            #print a, b
            try:
#                i = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                i = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.IMREAD_COLOR)
                cv2.imshow('i',i)
                

                if (self.onkeypress):
                    key = cv2.waitKey(1)
                    self.onkeypress(key)
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
 
    def setKeypress(self, func):
        self.onkeypress = func
        
    def startThread(self):
        self.myThread = threading.Thread(target=self.loop)
        self.myThread.start()