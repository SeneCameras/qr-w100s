#!/usr/bin/env python

import urllib2

import cv2
import multiprocessing
import Queue #needed separately for the Empty exception
import time, datetime

import sys
from PySide import QtGui, QtCore

import numpy as np

def printnow(string):
   print string
   sys.stdout.flush()

class SystemCamera1VideoProcess(multiprocessing.Process):
   def __init__(self, outputqueue):
      multiprocessing.Process.__init__(self)
      self.outputqueue = outputqueue
      self.exit = multiprocessing.Event()
      self.sleeping = multiprocessing.Event()

   def run(self):
      
      camera = cv2.VideoCapture(1)

      while not self.exit.is_set():
         
         if self.sleeping.is_set():
            time.sleep(0.1)
            continue

         hello, cv_img = camera.read()
         
         # resize to 320x240
         if (cv_img is not None) and cv_img.data:
            
            cv_img = cv2.resize(cv_img,(320,240),interpolation=cv2.INTER_NEAREST)
            
            vis = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            tstamp = datetime.datetime.now()
            try:
               self.outputqueue.put((tstamp, vis), False)
            except Queue.Full:
               time.sleep(1/30.0) #default to 30fps if nobody wants to go faster
               continue
      
      camera.release()

   def isAwake(self):
      return not self.sleeping.is_set()

   def shutdown(self):
      self.exit.set()
      
   def sleep(self):
      self.sleeping.set()
      
   def wake(self):
      self.sleeping.clear()

class WalkeraVideoProcess(multiprocessing.Process):
   
   def __init__(self, outputqueue):
      multiprocessing.Process.__init__(self)
      self.outputqueue = outputqueue
      self.exit = multiprocessing.Event()
      self.sleeping = multiprocessing.Event()
      
      self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()                
      self.top_level_url = "http://192.168.10.1:8080"
      
   def run(self):
      
      buffer = ''
      self.state = 0
      self.password_mgr.add_password(None, self.top_level_url, 'admin', 'admin123')
      self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
      self.opener = urllib2.build_opener(self.handler)
      try:
         self.opener.open("http://192.168.10.1:8080/?action=stream")
         urllib2.install_opener(self.opener)
         self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")            
      except Exception, e:
         print "exception opening Walkera stream in urllib2:", e
         sys.stdout.flush()
         self.exit.set()
         time.sleep(0.1)
      
      while not self.exit.is_set():
         
         if self.sleeping.is_set():
            time.sleep(0.1)
            continue

         data = self.resp.read(4096) #recv buffer
         buffer += data
         
         while buffer.find('\n') != -1: # delim='\n'
            line, buffer = buffer.split("\n", 1)
            if self.state==0:
               if line[0:20] == "--boundarydonotcross":
                  self.state = 1
            elif self.state==1:
               # print line.split(":")
               self.state = 2
            elif self.state==2:
               #print line
               datalength = int(line.split(":")[1][1:-1])
               self.state = 3
               #print buffer
            elif self.state==3:
               self.state = 4
               #walkera_timestamp = float(line.split(":")[1][1:-1])
               #print "timestamp:", walkera_timestamp
               sys.stdout.flush()
            else:
               while(len(buffer) < datalength):
                  bytes_remaining = datalength - len(buffer)
                  data = self.resp.read(bytes_remaining)
                  buffer += data
               self.state = 0
               
               #buffer contains one image
               try:
                  cv_img = cv2.imdecode(np.fromstring(buffer, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)
                  vis = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                  
               except Exception, e:
                  print Exception, e
                  sys.stdout.flush()
      
               tstamp = datetime.datetime.now()
               try:
                  self.outputqueue.put((tstamp, vis), False)
               except Queue.Full:
                  time.sleep(1/30.0) #default to 30fps if nobody wants to go faster
                  continue

   def isAwake(self):
      return not self.sleeping.is_set()

   def shutdown(self):
      self.exit.set()
      
   def sleep(self):
      self.sleeping.set()
      
   def wake(self):
      self.sleeping.clear()


class VideoTestWidget(QtGui.QWidget):
   def __init__(self, input_process_class, target_FPS=30.0):
      super(VideoTestWidget, self).__init__()

      self.process_output_queue  = multiprocessing.Queue(maxsize=1)
      self.process = input_process_class(self.process_output_queue)
      self.process.start()
      
      
      layout = QtGui.QGridLayout()
      self.pixmap = QtGui.QLabel()
      self.pixmap.setMinimumSize(320,240)
      self.pixmap.setMaximumSize(320,240)
      self.pixmap.setScaledContents(True)
      layout.addWidget(self.pixmap, 0, 0)
      self.setLayout(layout)

      self.draw_images_t = QtCore.QTimer()
      self.draw_images_t.timeout.connect(self.drawImage)
      self.draw_images_t.start(1000.0/target_FPS)
   
   def drawImage(self):
      try:
         tstamp, cv_img = self.process_output_queue.get(False)
         if len(cv_img.shape) > 2:
            height, width, bytesPerComponent = cv_img.shape
            bytesPerLine = bytesPerComponent * width;
            qimage = QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
         else:
            height, width = cv_img.shape
            qimage = QtGui.QImage(cv_img.data, width, height, QtGui.QImage.Format_Indexed8)
         self.pixmap.setPixmap(QtGui.QPixmap.fromImage(qimage))
      except Queue.Empty:
         pass
   
   def shutdown(self):
      self.process.shutdown()
      self.process.terminate()


if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   
   '''
   SystemCamera1VideoProcess
   WalkeraVideoProcess
   '''
   
   widget = VideoTestWidget(SystemCamera1VideoProcess)

   app.aboutToQuit.connect(widget.shutdown)

   widget.show()

   sys.exit(app.exec_())