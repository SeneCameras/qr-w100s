#!/usr/bin/env python

import cv2

from common import SleepableCVProcess

class IdentityProcess(SleepableCVProcess):
   def __init__(self, inputqueue, outputqueue):
      SleepableCVProcess.__init__(self, inputqueue, outputqueue)

   def doWork(self, cv_img):
         return cv_img
