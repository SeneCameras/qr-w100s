#!/usr/bin/env python

import cv2
import multiprocessing
import Queue #needed separately for the Empty exception
import datetime

class BGR2RGBProcess(multiprocessing.Process):
   def __init__(self, inputqueue, outputqueue):
      multiprocessing.Process.__init__(self)
      self.inputqueue = inputqueue
      self.outputqueue = outputqueue
      self.exit = multiprocessing.Event()

   def run(self):
      while not self.exit.is_set():
         try:
            tstamp, cv_img = self.inputqueue.get(False)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB, cv_img)
            tstamp = datetime.datetime.now()
            try:
               self.outputqueue.put((tstamp, cv_img), False)
            except Queue.Full:
               continue
         except Queue.Empty:
            continue
   def shutdown(self):
      self.exit.set()

