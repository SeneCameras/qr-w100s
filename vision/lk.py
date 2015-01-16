from common import anorm2, draw_str
import cv2
import time
import numpy as np
from multiprocessing import Process
lk_params = dict( winSize  = (15, 15),
                          maxLevel = 2,
                          criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 50,
                               qualityLevel = 0.3,
                               minDistance = 7,
                               blockSize = 7 )
class LKProcess(Process):
    def __init__(self, bufferqueue):
        Process.__init__(self)
        self.bufferqueue = bufferqueue
        self.running = True
        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.frame_gray = None
        self.prev_gray = None
        self.frame_idx = 0


    def run(self):
        while self.running:
            #print "blocking until we get a buffer"
            frame = self.bufferqueue.get(True) #block until new raw_frame
            #print "buffer got"
            startd = time.time()
            #frame = cv2.imdecode(np.fromstring(raw_frame.value, dtype=np.uint8),1)
            
            #TODO: sync the decoded image instead of raw jpeg
            
            start = time.time()
            vis = frame.copy()
            self.frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if len(self.tracks) > 0:
                img0, img1 = self.prev_gray, self.frame_gray
                p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
                p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
                p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
                d = abs(p0-p0r).reshape(-1, 2).max(-1)
                good = d < 1
                new_tracks = []
                deltax = []
                deltay = []
                dx = 0
                dy = 0
                
                for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
                    if not good_flag:
                        continue
                    deltax.append(x - tr[-1][0]) 
                    deltay.append(y - tr[-1][1])
                    tr.append((x, y))

                    
                    #print tr
                    if len(tr) > self.track_len:
                        del tr[0]
                    new_tracks.append(tr)
                    cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
                self.tracks = new_tracks
                cv2.polylines(vis, [np.int32(tr) for tr in self.tracks], False, (0, 255, 0))
                draw_str(vis, (20, 20), 'track count: %d' % len(self.tracks))
                if len(deltay)>0:
                    pass
                    #print "avg:",(sum(deltax)/len(deltax),sum(deltay)/len(deltay))
        #            print deltax
        #           print deltay
            if self.frame_idx % self.detect_interval == 0:
                mask = np.zeros_like(self.frame_gray)
                mask[:] = 255
                for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
                    cv2.circle(mask, (x, y), 5, 0, -1)
                p = cv2.goodFeaturesToTrack(self.frame_gray, mask = mask, **feature_params)
                if p is not None:
                    for x, y in np.float32(p).reshape(-1, 2):
                        self.tracks.append([(x, y)])
            self.frame_idx += 1
            self.prev_gray = self.frame_gray
            end = time.time()
            print 'lk latency', (end-start)*1000, 'ms', (end-startd)*1000, 'ms'
            #vis
            cv2.imshow('lk_track', vis)
        
        
            cv2.waitKey(1)