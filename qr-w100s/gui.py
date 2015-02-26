#!/usr/bin/env python

import sys
from PySide import QtGui, QtCore
import cv2
import time, datetime

import multiprocessing
import Queue #needed separately for the Empty exception

from vision.BGR2RGB import BGR2RGBProcess
from vision.lk import LKProcess

import numpy as np
import pyqtgraph as pg

#wrap up PlotWidget to pull (x,y) pairs from a queue
class TimeYQueuePlotWidget(pg.PlotWidget):
   def __init__(self, q, target_FPS = 30.0, name='plot'):
      super(TimeYQueuePlotWidget, self).__init__(name=name)
      self.q = q
      self.xvals = []
      self.yvals = []
      self.start = datetime.datetime.now()
      
      self.update_t = QtCore.QTimer()
      self.update_t.timeout.connect(self.update)
      self.update_t.start(1000.0/target_FPS)
      self.update_FPS = fps()
      
      self.p0 = self.plot()
      self.p0.setPen((200,200,100))
      self.setLabel('left', 'FPS', units='Hz')
      self.setLabel('bottom', 'Time', units='s')
      self.setXRange(0, 20)
      self.setYRange(0, 40)
      
   def update(self):
      self.update_FPS.update()
      #self.update_FPS.log()
      try:
         tstamp, y = self.q.get(False)
         self.xvals.append( (tstamp - self.start).total_seconds() )
         self.yvals.append(y)
         self.p0.setData(y=self.yvals, x=self.xvals)
      except Queue.Empty:
         pass

# iir filter on instantaneous frames per second
class fps():
   def __init__(self, log_queue = None):
      self.prev = datetime.datetime.now()
      self.FPS = 10.0 #guess
      self.q = None
      if log_queue:
         self.q = log_queue
   def update(self):
      now = datetime.datetime.now() 
      newFPS = 1.0 / (now - self.prev).total_seconds()
      self.prev = now
      self.FPS = self.FPS * 0.9 + newFPS * 0.1
      if self.q:
         try:
            self.q.put((self.prev, self.FPS), False)
         except Queue.Full:
            pass
   def log(self, label=""):
      print "%s %6.3f FPS" % (label, self.FPS)
      sys.stdout.flush()
   def get(self):
      return self.FPS

# manages a particular input stream and dispatches frames to VideoProcessWidgets
class VideoManagerWidget(QtGui.QWidget):
   def __init__(self, target_FPS = 30.0):
      super(VideoManagerWidget, self).__init__()
      
      self.camera = cv2.VideoCapture(1) # camera ID depends on system: 0, 1, etc
      self.get_images_t = QtCore.QTimer()
      self.get_images_t.timeout.connect(self.get_images)
      self.get_images_t.start(1000.0/target_FPS)
      self.get_images_FPS = fps()
      self.queues = [] # who wants data?
      
   def append(self, q):
      self.queues.append(q)
      
   def get_images(self):
      self.get_images_FPS.update()
      #self.get_images_FPS.log()
      hello, cv_img = self.camera.read()
      tstamp = datetime.datetime.now()
      for q in self.queues:
         try:
            q.put((tstamp, cv_img), False)
         except Queue.Full:
            pass
         
   def shutdown(self):
      self.camera.release()
      
# manages a single video stream processor and draws output
class VideoProcessorWidget(QtGui.QLabel):
   def __init__(self, process, q, q_fps=None, target_FPS = 30.0):
      super(VideoProcessorWidget, self).__init__()
      self.setScaledContents(True)
      
      self.draw_images_t = QtCore.QTimer()
      self.draw_images_t.timeout.connect(self.draw_images)
      self.draw_images_t.start(1000.0/target_FPS)
      self.draw_images_FPS = fps(log_queue = q_fps)
      self._q = q
      self._process = process
      self._process.start()
      
   def draw_images(self):
      self.draw_images_FPS.update()
      #self.draw_images_FPS.log()
      try:
         tstamp, cv_img = self._q.get(False)
         if len(cv_img.shape) > 2:
            height, width, bytesPerComponent = cv_img.shape
            bytesPerLine = bytesPerComponent * width;
            qimage = QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
         else:
            height, width = cv_img.shape
            qimage = QtGui.QImage(cv_img.data, width, height, QtGui.QImage.Format_Indexed8)
         self.setPixmap(QtGui.QPixmap.fromImage(qimage))
      except Queue.Empty:
         pass
      
   def shutdown(self):
      self._process.shutdown()
      time.sleep(0.1) #there's probably a better way, but this seems to work
      self._process.terminate()
      
class WalkeraGUI(QtGui.QWidget):
   def __init__(self):
      super(WalkeraGUI, self).__init__()

      self.shutdown_list = []

      tabs = QtGui.QTabWidget()
      tab1 = QtGui.QWidget()
      tab1_layout = QtGui.QGridLayout()
      
      self.vm = VideoManagerWidget()
      self.shutdown_list.append(self.vm.shutdown)
      
      self.raw_qout = multiprocessing.Queue(maxsize=10)
      self.raw_qin  = multiprocessing.Queue(maxsize=10)
      self.raw_fps_queue  = multiprocessing.Queue(maxsize=10)
      self.vm.append(self.raw_qout) #put cam frames out for raw processing
      self.raw_process = BGR2RGBProcess(self.raw_qout, self.raw_qin)
      self.raw_widget = VideoProcessorWidget(self.raw_process, self.raw_qin, q_fps=self.raw_fps_queue)
      tab1_layout.addWidget(self.raw_widget, 0, 0)
      self.shutdown_list.append(self.raw_widget.shutdown)
      
      self.raw_plot = TimeYQueuePlotWidget(self.raw_fps_queue)
      tab1_layout.addWidget(self.raw_plot, 1, 0)
      
      
      self.lk_qout = multiprocessing.Queue(maxsize=10)
      self.lk_qin  = multiprocessing.Queue(maxsize=10)
      self.lk_fps_queue  = multiprocessing.Queue(maxsize=10)
      self.vm.append(self.lk_qout) #put cam frames out for raw processing
      self.lk_process = LKProcess(self.lk_qout, self.lk_qin)
      self.lk_widget = VideoProcessorWidget(self.lk_process, self.lk_qin, q_fps=self.lk_fps_queue)
      tab1_layout.addWidget(self.lk_widget, 0, 1)
      self.shutdown_list.append(self.lk_widget.shutdown)
            
      self.lk_plot = TimeYQueuePlotWidget(self.lk_fps_queue)
      tab1_layout.addWidget(self.lk_plot, 1, 1)
      
      tab1.setLayout(tab1_layout)
      tabs.addTab(tab1,"CV")        

      #main window layout
      window_layout = QtGui.QBoxLayout(QtGui.QBoxLayout.LeftToRight, self)        
      window_layout.addWidget(tabs)

      self.setWindowTitle('Sene Cameras - QRW100S')
      self.move(50,50)
      self.resize(1200, 700)
      self.setLayout(window_layout)
      
   def shutdown(self):
      for f in self.shutdown_list:
         f()

if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   widget = WalkeraGUI()
   
   # raw video processing thread
   app.aboutToQuit.connect(widget.shutdown)

   widget.show()
   sys.exit(app.exec_())
   
