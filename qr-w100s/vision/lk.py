#!/usr/bin/env python

from common import anorm2, draw_str

import cv2
import multiprocessing
import Queue #needed separately for the Empty exception
import time, datetime
import numpy as np

lk_params = dict( winSize  = (15, 15),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 50,
                       qualityLevel = 0.3,
                       minDistance = 7,
                       blockSize = 7 )

from common import SleepableCVProcess

class LKProcess(SleepableCVProcess):
   def __init__(self, inputqueue, outputqueue):
      SleepableCVProcess.__init__(self, inputqueue, outputqueue)

      self.track_len = 10
      self.detect_interval = 5
      self.tracks = []
      self.frame_gray = None
      self.prev_gray = None
      self.frame_idx = 0

   def doWork(self, cv_img):
      try:
         self.frame_gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
         vis = self.frame_gray.copy()
         vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2RGB)
         
         if len(self.tracks) > 0:
            img0, img1 = self.prev_gray, self.frame_gray
            p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
            p1,  st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
            d = abs(p0-p0r).reshape(-1, 2).max(-1)
            good = d < 1
            new_tracks = []
            dx = 0
            dy = 0
            
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
 
         return vis
      
      except Exception, e:
         print "exception in lk:", e
         return cv_img
            