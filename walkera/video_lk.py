import urllib2
import time
import cv2
import numpy as np
import threading
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import os
import tkFileDialog

import video
from common import anorm2, draw_str
from time import clock

lk_params = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 50,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )


class Video:
    def __init__(self):
    
    #lk setup
        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.frame_idx = 0

    ###
    
        self.onkeypress = False
        self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        self.detectFaces = False
        self.DOWNSCALE = 4
        self.frontalclassifier = False
        
        self.top_level_url = "http://192.168.10.1:8080"
        self.password_mgr.add_password(None, self.top_level_url, 'admin', 'admin123')

        self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
        self.opener = urllib2.build_opener(self.handler)
        self.opener.open("http://192.168.10.1:8080/?action=stream")
        urllib2.install_opener(self.opener)
        print 'opening url'

        self.recording = False
        self.images = []
        
    def setClassifier(self, classifierxml):
        self.frontalclassifier = cv2.CascadeClassifier(classifierxml)


    def doLK(self, frame):
        #start = time.time()
        vis = frame.copy()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if len(self.tracks) > 0:
            img0, img1 = self.prev_gray, frame_gray
            p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
            p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
            d = abs(p0-p0r).reshape(-1, 2).max(-1)
            good = d < 1
            new_tracks = []
            for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
                if not good_flag:
                    continue
                tr.append((x, y))
                if len(tr) > self.track_len:
                    del tr[0]
                new_tracks.append(tr)
                cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
            self.tracks = new_tracks
            cv2.polylines(vis, [np.int32(tr) for tr in self.tracks], False, (0, 255, 0))
            draw_str(vis, (20, 20), 'track count: %d' % len(self.tracks))

        if self.frame_idx % self.detect_interval == 0:
            mask = np.zeros_like(frame_gray)
            mask[:] = 255
            for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
                cv2.circle(mask, (x, y), 5, 0, -1)
            p = cv2.goodFeaturesToTrack(frame_gray, mask = mask, **feature_params)
            if p is not None:
                for x, y in np.float32(p).reshape(-1, 2):
                    self.tracks.append([(x, y)])
        self.frame_idx += 1
        self.prev_gray = frame_gray
        #end = time.time()
        #print 'latency fps', 1/(end-start)
        cv2.imshow('lk_track', vis)

        #ch = 0xFF & cv2.waitKey(1)
        #if ch == 27:
        #    self.reading = False
        #    self.sock.close()
        #    del self.myThread
            
        #    exit(0)
        #    break
        
    def readframes(self, recv_buffer=4096, delim='\n'):
        buffer = ''
        data = True
        self.reading = True
        self.state = 0
        ts = 0
        print ' in readframes'
        while data and self.reading:
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
                    if self.root.quit_flag:
                        self.root.quit_flag = False
                        self.root.destroy()
                        exit(0)
                    yield buffer
        quit(0)


    def loop(self,image_label):
        self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")
        # self.resp = open('noFaceRecognized.avi','r')
        #print resp.read(10)
        size = 0
        #a = time.time()
        n = 1
        avg = 0
        x = 0

        for frame in self.readframes():
          
            #dump = open('dump/dumpframe'+str(x),'w')
            #x = x+1
            #dump.write(frame)
            #t = time.time()
            #fps = 1/(t-a)
            #print "frame len: ", len(frame)
            #print "FPS: ", fps
            #a = t

            #a = frame.find('\xff\xd8')
            #b = frame[-20:].find('\xff\xd9')
            #if b != -1:
            #    frame = frame[0:-20+b]
            #print a, b
            try:
                s = time.time()
                i = cv2.imdecode(np.fromstring(frame, dtype=np.uint8),1) # cv2.IMREAD_COLOR on PC = 1 = cv2.CV_LOAD_IMAGE_COLOR on mac. srsly
                self.doLK(i)
                print "whole thing", 1/(time.time()-s)
                #i = cv2.imdecode(np.fromstring(frame+'\xff\xd9', dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
                if i != None:
                    # i = cv2.imdecode(np.fromstring(frame, dtype=np.uint8),cv2.IMREAD_COLOR)
                    
                    if (self.detectFaces and self.frontalclassifier):
                    # detect faces
                        minisize = (i.shape[1]/self.DOWNSCALE,i.shape[0]/self.DOWNSCALE)
                        miniframe = cv2.resize(i, minisize)
                        frontalfaces = self.frontalclassifier.detectMultiScale(miniframe)
                        for f in frontalfaces:
                            x, y, w, h = [ v*self.DOWNSCALE for v in f ]
                        #     # draws bounding box
                            cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
                        if len(frontalfaces) >= 1:
                            x, y, w, h = [ v*self.DOWNSCALE for v in frontalfaces[0] ]
                            if i.shape[1]*(2/3.) < x+w/2:# too far right
                                cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255))
                        #         # print "turn counterclockwise"
                            elif i.shape[1]*(1/3.) > x+w/2: # too far left
                        #         # print "turn clockwise"
                                cv2.rectangle(i, (x,y), (x+w,y+h), (0,255,0))
                            else: # centered
                        #         # print "centered"
                                cv2.rectangle(i, (x,y), (x+w,y+h), (255,0,0))
                        #     print (x+w/2.),(y+h/2.),(w**2+h**2)**0.5
                    cv_image = cv2.cvtColor(i, cv2.COLOR_BGR2RGB)
                    pil_image = PIL.Image.fromarray(cv_image)
                    tk_image = PIL.ImageTk.PhotoImage(image=pil_image)
                    if self.recording:
                        self.images += [i]
                    image_label.configure(image=tk_image)
                    image_label._image_cache = tk_image  # avoid garbage collection
                    self.root.update()
                    
                    #key = cv2.waitKey(1)
                    #if (key != -1 and self.onkeypress):
                    #    self.onkeypress(key)
                    #if key==27:
                    #    self.reading = False
                    #    del self.myThread
                    #    exit(0)
                
            except Exception, e:
                print "EXCEPTION:", e  
                raise e
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
        self.root.bind("<Key>", lambda k: self.onkeypress(k.keycode))

    def askdirectory(self):
        # defining options for opening a directory
        dir_opt = options = {}
        options['initialdir'] = 'C:\\'
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'Title'

        """Returns a selected directoryname."""
        if self.recording == True:
            print 'saving'
            self.recording = False
            directory = tkFileDialog.askdirectory(**dir_opt) + '/arbitrary'
            print "Location of folder:", directory
            if not os.path.exists(directory): os.makedirs(directory)
            # f = open(directory+'/image.jpeg','w')
            # print 
            imageNames = ''
            for x in range(len(self.images)):
                cv2.imwrite(directory+'/image%s.jpg' % x,self.images[x])
                imageNames += 'image%s.jpg ,\n\r' % x
            fileText = '[\n\r' + imageNames + ']'
            newFile = open(directory+'/images.txt', 'w')
            newFile.write(fileText)

    def startRecording(self):
        if self.recording == False:
            print "recording"
            self.recording = True

    def startThread(self):
        self.root = tk.Tk()
        def set_quit_flag():
            self.root.quit_flag = True
        self.root.bind('<Escape>', lambda e: set_quit_flag())  
        self.root.bind("<KeyRelease-s>", lambda e: self.askdirectory())  
        self.root.bind("<KeyRelease-r>", lambda e: self.startRecording())
        setattr(self.root, 'quit_flag', False)    
        self.root.protocol('WM_DELETE_WINDOW', set_quit_flag)
        image_label = tk.Label(master=self.root)  # label for the video frame
        image_label.pack()
        self.root.after(0, func=lambda: self.loop(image_label))

        
        self.myThread = threading.Thread(target=self.root.mainloop)
        self.myThread.start()