#!/usr/bin/env python

import cv2

from common import SleepableCVProcess

class BGR2RGBProcess(SleepableCVProcess):
   def __init__(self, inputqueue, outputqueue):
      SleepableCVProcess.__init__(self, inputqueue, outputqueue)

   def doWork(self, cv_img):
      try:
         vis = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
         return vis
      
      except Exception, e:
         print "exception in bgr2rgb:", e
         return cv_img