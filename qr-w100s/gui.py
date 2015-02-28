#!/usr/bin/env python

import sys
from PySide import QtGui, QtCore
import cv2
import time, datetime

import multiprocessing
import Queue #needed separately for the Empty exception

from vision.BGR2RGB import BGR2RGBProcess
from vision.lk import LKProcess
from vision.facedetect import FaceDetectProcess

from input.joystick import JoystickProcess

import numpy as np
import pyqtgraph as pg

import inspect
def debug():
    (frame, filename, line_number,
     function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
    print(frame, filename, line_number, function_name, lines, index)
    sys.stdout.flush()
def printnow(string):
   print string
   sys.stdout.flush()

# multiprocessing wrapper Widget 
class ProcessorWidget(QtGui.QWidget):
   def __init__(self, process_class):
      super(ProcessorWidget, self).__init__()
      self.process_class = process_class
      self.managed_objects = []
   def start(self, input_queue, output_queue):
      self.process = self.process_class(input_queue, output_queue)
      self.process.start()
      self.managed_objects.append(self.process)
   def manageSleepableWidget(self, w):
      self.managed_objects.append(w)
   def isAwake(self):
      #everybody sleeps together
      return self.process.isAwake()
   def sleep(self):
      for o in self.managed_objects:
         if o.isAwake():
            o.sleep()
   def wake(self):
      for o in self.managed_objects:
         if not o.isAwake():
            o.wake()
   def shutdown(self):
      for o in self.managed_objects:
         o.shutdown()
         try: # see if terminate() exists
            o.terminate
         except NameError:
            pass
         else:
            time.sleep(0.1)
            o.terminate()

# maintain a simple iir filter on instantaneous frames per second
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
   def reset(self):
      self.prev = datetime.datetime.now()
      # try to clear the queue
      if self.q:
         try:
            tstamp, y = self.q.get(False)
         except Queue.Empty:
            pass
      time.sleep(0.001) #some laziness here to avoid div/0
   def log(self, label=""):
      print "%s %6.3f FPS" % (label, self.FPS)
      sys.stdout.flush()
   def get(self):
      return self.FPS

# manages a single video stream processor
class VideoProcessorWidget(ProcessorWidget):
   def __init__(self, process_class, process_label="", FPS_plot = True, target_FPS = 30.0):
      super(VideoProcessorWidget, self).__init__(process_class)
      
      self.process_input_queue   = multiprocessing.Queue(maxsize=1)
      self.process_output_queue  = multiprocessing.Queue(maxsize=1)
      self.start(self.process_input_queue, self.process_output_queue)

      layout = QtGui.QGridLayout()

      self.toggle = QtGui.QCheckBox("Enable " + process_label)
      layout.addWidget(self.toggle, 0, 0)
      self.toggle.setChecked(True)
      self.toggle.stateChanged.connect(self.toggleChange)
      
      self.pixmap = QtGui.QLabel()
      self.pixmap.setMinimumSize(320,240)
      self.pixmap.setMaximumSize(320,240)
      self.pixmap.setScaledContents(True)
      layout.addWidget(self.pixmap, 1, 0)
      
      self.plot = None
      if FPS_plot:
         self.fps_queue  = multiprocessing.Queue(maxsize=1)
         self.FPS = fps(log_queue = self.fps_queue)
         self.plot = TimeYQueuePlotWidget(self.fps_queue)
         self.manageSleepableWidget(self.plot)
         layout.addWidget(self.plot, 2, 0)
         
      self.setLayout(layout)
      
      self.draw_images_t = QtCore.QTimer()
      self.draw_images_t.timeout.connect(self.drawImage)
      self.draw_images_t.start(1000.0/target_FPS)
      
   def toggleChange(self):
      if self.toggle.isChecked():
         if not self.isAwake():
            self.wake()
      else:
         if self.isAwake():
            self.sleep()

   def drawImage(self):
      try:
         tstamp, cv_img = self.process_output_queue.get(False)
         if self.plot is not None:
            self.FPS.update() #only count when we successfully get a frame!
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

# manages the input streams and dispatches frames to consumer processes
class VideoManagerWidget(QtGui.QWidget):
   def __init__(self, target_FPS = 30.0):
      super(VideoManagerWidget, self).__init__()
           
      self.managed_processor_widgets = []
      self.consumer_queues = []
      
      #selector for video input type
      layout = QtGui.QHBoxLayout()
      self.src_type_group = QtGui.QButtonGroup()
      self.r0=QtGui.QRadioButton("Camera(1)")
      self.src_type_group.addButton(self.r0, 0)
      self.r0.clicked.connect(self.switchToCamera1)
      self.r1=QtGui.QRadioButton("Walkera Wifi (FUTURE)")
      self.src_type_group.addButton(self.r1, 1)
      self.r1.clicked.connect(self.switchToWalkeraWifi)
      self.r2=QtGui.QRadioButton("None")
      self.src_type_group.addButton(self.r2, 2)
      self.r2.clicked.connect(self.switchToNone)
      layout.addWidget(self.r0)
      layout.addWidget(self.r1)
      layout.addWidget(self.r2)
      self.setLayout(layout)
      
      # default to cam1 video
      self.r1.setEnabled(False)
      self.r0.setChecked(True)  
      self.camera = cv2.VideoCapture(1) # camera ID depends on system: 0, 1, etc
      
      self.get_images_t = QtCore.QTimer()
      self.get_images_t.timeout.connect(self.getImage)
      self.get_images_t.start(1000.0/target_FPS)
      
      self.get_images_FPS = fps()

   def createVideoProcessorWidget(self, process_class, process_label=""):
      new_vp_widget = VideoProcessorWidget(process_class, process_label)
      self.consumer_queues.append(new_vp_widget.process_input_queue)
      self.managed_processor_widgets.append(new_vp_widget)
      return new_vp_widget
   
   def getImage(self):
      if self.src_type_group.checkedId() == 0: #cam1
         try:
            hello, cv_img = self.camera.read()
            self.get_images_FPS.update()
            
            # resize to 320x240
            if (cv_img is not None) and cv_img.data:
               cv_img = cv2.resize(cv_img,(320,240),interpolation=cv2.INTER_NEAREST)
            
            tstamp = datetime.datetime.now()
            for q in self.consumer_queues:
               try:
                  q.put((tstamp, cv_img), False)
               except Queue.Full:
                  pass
         except:
            pass

   def shutdown(self):
      if self.src_type_group.checkedId() == 0:
         self.camera.release()
      
   def switchToCamera1(self):
      if self.src_type_group.checkedId() != 0:
         self.camera = cv2.VideoCapture(1)
   
   def switchToWalkeraWifi(self):
      pass
   
   def switchToNone(self):
      if self.src_type_group.checkedId() == 0:
         self.camera.release()


#wrap up PlotWidget to pull (datetime, y) pairs from a queue
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
      self.setYRange(0, 30)
      
      self.awake = True
      
   def update(self):
      try:
         tstamp, y = self.q.get(False)
         self.update_FPS.update()
         self.xvals.append( (tstamp - self.start).total_seconds() )
         self.yvals.append(y)
         self.p0.setData(y=self.yvals, x=self.xvals)
      except Queue.Empty:
         pass
      
   def idle(self):
      pass
   
   def isAwake(self):
      return self.awake
      
   def sleep(self):
      self.update_t.timeout.connect(self.idle)
      self.awake = False
      
   def wake(self):
      self.update_FPS.reset()
      self.start = datetime.datetime.now()
      time.sleep(0.001)
      self.update_FPS.update()
      self.xvals = []
      self.yvals = []
      self.update_t.timeout.connect(self.update)
      self.awake = True

   def shutdown(self):
      pass

class WalkeraGUI(QtGui.QWidget):
   def __init__(self):
      super(WalkeraGUI, self).__init__()

      self.objects_to_shutdown_at_quit = []

      tabs = QtGui.QTabWidget()
      
      tab1 = QtGui.QWidget()
      tab1_layout = QtGui.QGridLayout()
      
      self.vm = VideoManagerWidget()
      tab1_layout.addWidget(self.vm, 0, 0, 1, 3)
      self.objects_to_shutdown_at_quit.append(self.vm)
      
      self.raw_widget = self.vm.createVideoProcessorWidget(BGR2RGBProcess, process_label="Raw Video")
      tab1_layout.addWidget(self.raw_widget, 1, 0)
      self.objects_to_shutdown_at_quit.append(self.raw_widget)
      
      self.lk_widget = self.vm.createVideoProcessorWidget(LKProcess, process_label="Optical Flow")
      tab1_layout.addWidget(self.lk_widget, 1, 1)
      self.objects_to_shutdown_at_quit.append(self.lk_widget)

      self.fd_widget = self.vm.createVideoProcessorWidget(FaceDetectProcess, process_label="Face Detection")
      tab1_layout.addWidget(self.fd_widget, 1, 2)
      self.objects_to_shutdown_at_quit.append(self.fd_widget)
      
      tab1.setLayout(tab1_layout)
      tabs.addTab(tab1, "CV")
      
      # 4-axis flight controls
      self.flight_control_widget = FlightControlWidget()
      self.objects_to_shutdown_at_quit.append(self.flight_control_widget)
      tabs.addTab(self.flight_control_widget, "Flight Controls")
      
      
      #main window layout
      window_layout = QtGui.QHBoxLayout()
      window_layout.addWidget(tabs)
      
      self.setWindowTitle('Sene Cameras - QR-W100S')
      self.move(50,50)
      self.resize(1000, 550)
      self.setLayout(window_layout)
      
   def shutdown(self):
      for o in self.objects_to_shutdown_at_quit:
         o.shutdown()


# a class to manage a PID controller with nice plotting
class ControlWidget(QtGui.QWidget):
   def __init__(self, textlabel = "Controller", minval = 0.0, maxval = 1.0):
      super(ControlWidget, self).__init__()
      
      self._minval = minval
      self._maxval = maxval
      
      self.label_widget = QtGui.QLabel()
      self.label_widget.setText(textlabel)
      
      self.history_plot_q  = multiprocessing.Queue(maxsize=1)
      self.history_plot_widget = TimeYQueuePlotWidget(self.history_plot_q)
      self.history_plot_widget.setMaximumSize(300,240)
      self.history_plot_widget.setYRange(self._minval, self._maxval)
      self.history_plot_widget.setLabel('left', 'Setpoint', units='au')
      
      self.bar_plot_widget = pg.PlotWidget()
      self.bar_plot_widget.setMaximumSize(100,240)
      self.bar_plot_widget.hideAxis('bottom')
      self.bar_plot_widget.setXRange(-0.5, 0.5)
      self.bar_plot_widget.setYRange(self._minval, self._maxval)
      
      x = [0]
      y = [1.0] #power
      self.bg = pg.BarGraphItem(x=x, height=y, width=0.3, brush='r')
      self.bar_plot_widget.addItem(self.bg)
            
      layout = QtGui.QGridLayout()
      layout.addWidget(self.label_widget, 0, 0, 1, 2)
      layout.addWidget(self.history_plot_widget, 1, 0)
      layout.addWidget(self.bar_plot_widget, 1, 1)
      
      self.setLayout(layout)

# converts Joystick controls to four drone flight vectors
class FlightControlWidget(QtGui.QWidget):
   def __init__(self, target_FPS = 60.0):
      super(FlightControlWidget, self).__init__()
      self.process_output_queue = multiprocessing.Queue(maxsize=1)
      self.process = JoystickProcess(self.process_output_queue)
      self.process.start()

      self.get_joystick_inputs = QtCore.QTimer()
      self.get_joystick_inputs.timeout.connect(self.getJoystickInput)
      self.get_joystick_inputs.start(1000.0/target_FPS)
      
      layout = QtGui.QGridLayout()
      self.thrustwidget = ControlWidget(textlabel="thrust")
      layout.addWidget(self.thrustwidget, 0, 0)
      self.pitchwidget = ControlWidget(textlabel="pitch")
      layout.addWidget(self.pitchwidget, 0, 1)
      self.rollwidget = ControlWidget(textlabel="roll")
      layout.addWidget(self.rollwidget, 1, 0)
      self.yawwidget = ControlWidget(textlabel="raw")
      layout.addWidget(self.yawwidget, 1, 1)
      self.setLayout(layout)
      
   def isAwake(self):
      return self.process.isAwake()
   def sleep(self):
      if self.isAwake():
         self.process.sleep()
   def wake(self):
      if not self.isAwake():
         self.process.wake()
   def shutdown(self):
      self.process.shutdown()
      time.sleep(0.1)
      self.process.terminate()      
   def getJoystickInput(self):
      try:
         tstamp, data = self.process_output_queue.get(False)
         print tstamp, data
         sys.stdout.flush()
      except Queue.Empty:
         pass



if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   widget = WalkeraGUI()
   
   # raw video processing thread
   app.aboutToQuit.connect(widget.shutdown)

   widget.show()

   sys.exit(app.exec_())
   
