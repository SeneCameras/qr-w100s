#!/usr/bin/env python

import sys,os
from PySide import QtGui, QtCore
import cv2
import time, datetime

import multiprocessing
import Queue #needed separately for the Empty exception

from vision.identity import IdentityProcess
from vision.lk import LKProcess
from vision.facedetect import FaceDetectProcess
from vision.calibration import CameraCalibrator

from input.joystick import JoystickProcess
from input.video import SystemCamera0VideoProcess, SystemCamera1VideoProcess, WalkeraVideoProcess

from control.command import WalkeraCommandThread

import numpy as np
import pyqtgraph as pg

import binascii
import socket

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
   def start(self, input_queue = None, output_queue = None):
      if (output_queue is not None) and (input_queue is not None):
         self.process = self.process_class(input_queue, output_queue)
      elif (output_queue is not None):
         self.process = self.process_class(output_queue)
      else:
         self.process = self.process_class()
      self.process.start()
      self.managed_objects.append(self.process)
   def manageSleepableWidget(self, w):
      self.managed_objects.append(w)
   def isAwake(self):
      #everybody sleeps together
      return self.process.isAwake()
   def sleep(self):
      for o in self.managed_objects:
         if (o is not None) and o.isAwake():
            o.sleep()
   def wake(self):
      for o in self.managed_objects:
         if (o is not None) and not o.isAwake():
            o.wake()
   def reset(self):
      for o in self.managed_objects:
         if (o is not None):
            o.reset()
   def shutdown(self):
      for o in self.managed_objects:
         #print o
         if (o is not None):
            o.shutdown()
            try: # see if terminate() exists
               o.terminate
            except (NameError, AttributeError):
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

# manages a stack of snapshots for calibration purposes
class VideoCalibrationWidget(QtGui.QWidget):
   def __init__(self):
      super(VideoCalibrationWidget, self).__init__()

      self.snapshot_input_queue = multiprocessing.Queue(maxsize=1)
      self.snapshot_images = []
      self.snapshot_tstamps = []
      self.active_index = -1

      layout = QtGui.QGridLayout()
      
      cycle_left_button = QtGui.QPushButton('<', self)
      cycle_left_button.clicked.connect(self.cycleLeft)
      layout.addWidget(cycle_left_button, 0, 0)
      cycle_left_button.resize(cycle_left_button.sizeHint())

      self.pixmap = QtGui.QLabel()
      self.pixmap.setMinimumSize(320,240)
      self.pixmap.setMaximumSize(320,240)
      self.pixmap.setScaledContents(True)
      layout.addWidget(self.pixmap, 0, 1)

      cycle_right_button = QtGui.QPushButton('>', self)
      cycle_right_button.clicked.connect(self.cycleRight)
      layout.addWidget(cycle_right_button, 0, 2)
      cycle_right_button.resize(cycle_right_button.sizeHint())
      
      self.current_snapshot_label = QtGui.QLabel()
      self.current_snapshot_label.setText("DateTime - Frame 0")
      layout.addWidget(self.current_snapshot_label, 1, 0, 1, 3)
      
      collect_snapshot_button = QtGui.QPushButton('Take Snapshot', self)
      collect_snapshot_button.clicked.connect(self.collectSnapshot)
      collect_snapshot_button.resize(collect_snapshot_button.sizeHint())
      layout.addWidget(collect_snapshot_button, 2, 0, 1, 3)
      
      drop_snapshot_button = QtGui.QPushButton('Drop Snapshot', self)
      drop_snapshot_button.clicked.connect(self.dropSnapshot)
      drop_snapshot_button.resize(drop_snapshot_button.sizeHint())
      layout.addWidget(drop_snapshot_button, 3, 0, 1, 3)
      
      process_snapshots_button = QtGui.QPushButton('Calibrate lens using these Snapshots', self)
      process_snapshots_button.clicked.connect(self.processSnapshots)
      process_snapshots_button.resize(process_snapshots_button.sizeHint())
      layout.addWidget(process_snapshots_button, 4, 0, 1, 3)
      
      save_snapshots_button = QtGui.QPushButton('Save this set of Snapshots', self)
      save_snapshots_button.clicked.connect(self.saveSnapshots)
      save_snapshots_button.resize(save_snapshots_button.sizeHint())
      layout.addWidget(save_snapshots_button, 5, 0, 1, 3)
      
      load_snapshots_button = QtGui.QPushButton('Load a saved set of Snapshots', self)
      load_snapshots_button.clicked.connect(self.loadSnapshots)
      load_snapshots_button.resize(load_snapshots_button.sizeHint())
      layout.addWidget(load_snapshots_button, 6, 0, 1, 3)
      
      self.setLayout(layout)
      
      self.calibrator = CameraCalibrator()
      self.image_points = []
      
      self.cameraMatrix = [[400,0,160],[400,1,120],[0,0,1]] #guess at f=400pixels
      self.distCoeffs = [0,0,0,0,0] #k1, k2, p1, p2, k3
      
   def undistort(self, cv_img):
      return cv2.undistort(cv_img, self.cameraMatrix, self.distCoeffs)

   def collectSnapshot(self):
      self.image_points = []
      try:
         tstamp, cv_img = self.snapshot_input_queue.get(False)
         self.snapshot_images.append(cv_img.copy())
         self.snapshot_tstamps.append(tstamp)
         self.active_index = len(self.snapshot_images) - 1
         self.updateSnapshot()
      except Queue.Empty:
         printnow("No snapshots are available!")
   def saveSnapshots(self): 
      directory = QtGui.QFileDialog.getExistingDirectory(self, "Save Calibration Images", ".", QtGui.QFileDialog.ShowDirsOnly)
      if directory:
          print "Saving calibration images to %s"%directory
      for i, image in enumerate(self.snapshot_images):
         epoch = datetime.datetime.utcfromtimestamp(0)
         delta = self.snapshot_tstamps[i] - epoch
         filename = "%d"%(delta.total_seconds()*1000) + ".png"
         try:
            cv2.imwrite( os.path.join(directory, filename) , self.snapshot_images[i])
         except Exception  as e:
            print 'Exception occurred, value:', e.value
         else:
            print 'SAVE FILE [%d]'%i, os.path.join(directory, filename)
   def loadSnapshots(self):
      directory = QtGui.QFileDialog.getExistingDirectory(self, "Load Calibration Images", ".")
      if directory:
          print "Loading calibration images from %s"%directory
      i = 0
      self.snapshot_images = []
      self.snapshot_tstamps = []
      for filename in os.listdir(directory):
         if filename.endswith(".png"):
            print 'LOAD FILE [%d]'%i, os.path.join(directory, filename)
            i += 1
            self.snapshot_images.append(cv2.imread(os.path.join(directory, filename)))
            milliseconds = os.path.splitext(os.path.basename(filename))[0]
            self.snapshot_tstamps.append(datetime.datetime.utcfromtimestamp(float(milliseconds)/1000.0))
      self.active_index = len(self.snapshot_images) - 1 
      self.updateSnapshot()
   def dropSnapshot(self):
      self.image_points = []
      if len(self.snapshot_images) > 0:
         del self.snapshot_images[self.active_index]
         del self.snapshot_tstamps[self.active_index]
         if self.active_index == len(self.snapshot_images):
            self.active_index -= 1
         if self.active_index < 0:
            self.active_index = 0
         if len(self.snapshot_images)<1:
            self.pixmap.setPixmap(None)
            self.current_snapshot_label.setText("")
         else:
            self.updateSnapshot()
   def processSnapshots(self):
      self.image_points = []
      for image in self.snapshot_images:
         self.image_points.append(self.calibrator.findCorners(image))
      cameraMatrix, distCoeffs = self.calibrator.calibrate(self.image_points)
      if cameraMatrix is not None and distCoeffs is not None:
          self.cameraMatrix = cameraMatrix
          self.distCoeffs = distCoeffs
      self.updateSnapshot(self)
   def cycleRight(self):
      if self.active_index < ( len(self.snapshot_images)-1 ):
         self.active_index += 1
         self.updateSnapshot()
   def cycleLeft(self):
      if self.active_index > 0:
         self.active_index -= 1
         self.updateSnapshot()
   def updateSnapshot(self, image_points = None):
      if self.active_index >= 0:
         if self.active_index < len(self.snapshot_images):
            
            cv_img = self.snapshot_images[self.active_index]
            
            if len(self.image_points) > 0:
               cv_img = self.calibrator.drawCorners(cv_img,self.image_points[self.active_index])
               
            if len(cv_img.shape) > 2:
               height, width, bytesPerComponent = cv_img.shape
               bytesPerLine = bytesPerComponent * width;
               qimage = QtGui.QImage(cv_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            else:
               height, width = cv_img.shape
               qimage = QtGui.QImage(cv_img.data, width, height, QtGui.QImage.Format_Indexed8)
            
            self.pixmap.setPixmap(QtGui.QPixmap.fromImage(qimage))
            label = self.snapshot_tstamps[self.active_index].strftime("%A, %B %d, %Y . %I:%M:%f %p")
            self.current_snapshot_label.setText("[#%d] : "%self.active_index + label)
   def shutdown(self):
      self.snapshot_input_queue.cancel_join_thread()
         
# manages a single video stream processor
class VideoProcessorWidget(ProcessorWidget):
   def __init__(self, process_class, process_label="", FPS_plot = True, target_FPS = 30.0):
      super(VideoProcessorWidget, self).__init__(process_class)
      
      self.process_input_queue   = multiprocessing.Queue(maxsize=1)
      self.process_output_queue  = multiprocessing.Queue(maxsize=1)
      self.start( input_queue = self.process_input_queue, output_queue = self.process_output_queue)

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
      
      self.fps_plot = None
      if FPS_plot:
         self.fps_queue  = multiprocessing.Queue(maxsize=1)
         self.FPS = fps(log_queue = self.fps_queue)
         self.fps_plot = TimeYQueuePlotWidget(self.fps_queue)
         self.manageSleepableWidget(self.fps_plot)
         layout.addWidget(self.fps_plot, 2, 0)
         
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
         if self.fps_plot is not None:
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

# manages the two input streams and dispatches frames to consumer processes
class VideoManagerWidget(QtGui.QWidget):
   def __init__(self, target_FPS = 30.0):
      super(VideoManagerWidget, self).__init__()
      
      self.managed_processor_widgets = []
      self.managed_snapshot_widgets = []
      
      self.camera_queue0  = multiprocessing.Queue(maxsize=1)
      self.camera_process0 = SystemCamera0VideoProcess(self.camera_queue0)
      self.camera_process0.start()
      
      self.camera_queue1  = multiprocessing.Queue(maxsize=1)
      self.camera_process1 = SystemCamera1VideoProcess(self.camera_queue1)
      self.camera_process1.start()
   
      self.walkera_queue   = multiprocessing.Queue(maxsize=1)
      self.walkera_process = WalkeraVideoProcess(self.walkera_queue)
      self.walkera_process.start()
      
      layout = QtGui.QGridLayout()
      #selector for video input type
      self.src_type_group = QtGui.QButtonGroup()
      self.r0=QtGui.QRadioButton("Camera(0)")
      self.src_type_group.addButton(self.r0, 0)
      self.r0.clicked.connect(self.switchToCamera0)
      self.r1=QtGui.QRadioButton("Camera(1)")
      self.src_type_group.addButton(self.r1, 1)
      self.r1.clicked.connect(self.switchToCamera1)
      self.r2=QtGui.QRadioButton("Walkera Wifi")
      self.src_type_group.addButton(self.r2, 2)
      self.r2.clicked.connect(self.switchToWalkera)
      self.r3=QtGui.QRadioButton("None")
      self.src_type_group.addButton(self.r3, 3)
      
      layout.addWidget(self.r0, 0, 0, 1, 1) #row, col, rspan, cspan
      layout.addWidget(self.r1, 0, 1, 1, 1) #row, col, rspan, cspan
      layout.addWidget(self.r2, 0, 2, 1, 1) #row, col, rspan, cspan
      layout.addWidget(self.r3, 0, 3, 1, 1) #row, col, rspan, cspan
      
      #add a horizontal separator line
      hline_label = QtGui.QLabel()
      hline_label.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)
      hline_label.setLineWidth(1)
      layout.addWidget(hline_label, 1, 0, 1, 4)
      
      self.correct_distortion_checkbox = QtGui.QCheckBox("Apply Lens Calibration")
      self.correct_distortion_checkbox.setChecked(False)
      layout.addWidget(self.correct_distortion_checkbox, 2, 0, 1, 4) #row, col, rspan, cspan

      self.setLayout(layout)
      
      self.get_images_t = QtCore.QTimer()
      self.get_images_t.timeout.connect(self.getImage)
      self.get_images_t.start(1000.0/target_FPS)
      
      self.get_images_FPS = fps()
      
      # default to cam1 video
      self.r0.setChecked(True)

   def createVideoProcessorWidget(self, process_class, process_label="",  FPS_plot = True):
      new_vp_widget = VideoProcessorWidget(process_class, process_label, FPS_plot)
      self.managed_processor_widgets.append(new_vp_widget)
      return new_vp_widget
   
   def createVideoCalibrationWidget(self):
      self.calibration_widget = VideoCalibrationWidget()
      self.managed_snapshot_widgets.append(self.calibration_widget)
      return self.calibration_widget
   
   def getImage(self):
      if self.src_type_group.checkedId() == 3: #no video
         return
      
      if self.src_type_group.checkedId() == 0: #cam0
         try:
            tstamp, cv_img = self.camera_queue0.get(False)
            self.get_images_FPS.update()
         except:
            return
         
      elif self.src_type_group.checkedId() == 1: #cam1
         try:
            tstamp, cv_img = self.camera_queue1.get(False)
            self.get_images_FPS.update()
         except:
            return
         
      elif self.src_type_group.checkedId() == 2: #walkera
         try:
            tstamp, cv_img = self.walkera_queue.get(False)
            self.get_images_FPS.update()
         except:
            return
         
      #undistort here!
      if self.correct_distortion_checkbox.isChecked():
         cv_img = self.calibration_widget.undistort(cv_img)
      
      for w in self.managed_processor_widgets:
         try:
            w.process_input_queue.put((tstamp, cv_img), False)
         except Queue.Full:
            pass
         
      for w in self.managed_snapshot_widgets:
         try:
            w.snapshot_input_queue.put((tstamp, cv_img), False)
         except Queue.Full:
            w.snapshot_input_queue.get()
            w.snapshot_input_queue.put((tstamp, cv_img), False)

   def switchToCamera0(self):
      for w in self.managed_processor_widgets:
         w.reset()
   
   def switchToCamera1(self):
      for w in self.managed_processor_widgets:
         w.reset()
   
   def switchToWalkera(self):
      for w in self.managed_processor_widgets:
         w.reset()

   def shutdown(self):
      for w in self.managed_processor_widgets:
         w.shutdown()
      
      for w in self.managed_snapshot_widgets:
         w.shutdown()
      
      self.camera_process0.shutdown()
      time.sleep(0.1)
      self.camera_process0.terminate()
      
      self.camera_process1.shutdown()
      time.sleep(0.1)
      self.camera_process1.terminate()
      
      self.walkera_process.shutdown()
      time.sleep(0.1)
      self.walkera_process.terminate()

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
         self.xvals.append( (tstamp - self.start).total_seconds() )
         self.yvals.append(y)
         self.p0.setData(y=self.yvals, x=self.xvals)
      except Queue.Empty:
         pass
      
      #reduce to 100 points
      if len(self.xvals)>2 and len(self.yvals)>2:
         self.xvals = self.xvals[-150:]
         self.yvals = self.yvals[-150:]
         self.setXRange(self.xvals[0], self.xvals[-1:][0])
      
   def idle(self):
      pass
   
   def isAwake(self):
      return self.awake
      
   def sleep(self):
      self.update_t.timeout.connect(self.idle)
      self.awake = False
      
   def wake(self):
      self.update_t.timeout.connect(self.update)
      self.awake = True
      
   def reset(self):
      self.start = datetime.datetime.now()
      self.xvals = []
      self.yvals = []
      
   def shutdown(self):
      pass

# connects Joystick controls to drone flight vectors
class FlightControlWidget(ProcessorWidget):
   def __init__(self, target_FPS = 40.0, gui=None):
      self.process_class = JoystickProcess;
      super(FlightControlWidget, self).__init__(self.process_class)
      
      self.gui = gui
      
      self.joystick_process_output_queue  = multiprocessing.Queue(maxsize=1)
      self.start( input_queue = None, output_queue = self.joystick_process_output_queue)
      
      self.controller = None #turn this on later

      self.plot_x_size = 430
      self.plot_y_size = 240

      layout = QtGui.QGridLayout()

      self.thrust_label = QtGui.QLabel()
      self.thrust_label.setText("Thrust")
      layout.addWidget(self.thrust_label, 0, 0)
      
      self.thrust_queue = Queue.Queue(maxsize=1)
      self.thrust_widget = TimeYQueuePlotWidget(self.thrust_queue)
      self.manageSleepableWidget(self.thrust_widget)
      self.thrust_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.thrust_widget.setYRange(-1.1, 1.1)
      self.thrust_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.thrust_widget, 1, 0)
      
      self.yaw_label = QtGui.QLabel()
      self.yaw_label.setText("Yaw")
      layout.addWidget(self.yaw_label, 2, 0)
      
      self.yaw_queue = Queue.Queue(maxsize=1)
      self.yaw_widget = TimeYQueuePlotWidget(self.yaw_queue)
      self.manageSleepableWidget(self.yaw_widget)
      self.yaw_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.yaw_widget.setYRange(-1.1, 1.1)
      self.yaw_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.yaw_widget, 3, 0)

      self.pitch_label = QtGui.QLabel()
      self.pitch_label.setText("Pitch")
      layout.addWidget(self.pitch_label, 0, 1)
      
      self.pitch_queue = Queue.Queue(maxsize=1)
      self.pitch_widget = TimeYQueuePlotWidget(self.pitch_queue)
      self.manageSleepableWidget(self.pitch_widget)
      self.pitch_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.pitch_widget.setYRange(-1.1, 1.1)
      self.pitch_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.pitch_widget, 1, 1)
      
      self.roll_label = QtGui.QLabel()
      self.roll_label.setText("Roll")
      layout.addWidget(self.roll_label, 2, 1)
      
      self.roll_queue = Queue.Queue(maxsize=1)
      self.roll_widget = TimeYQueuePlotWidget(self.roll_queue)
      self.manageSleepableWidget(self.roll_widget)
      self.roll_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.roll_widget.setYRange(-1.1, 1.1)
      self.roll_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.roll_widget, 3, 1)

      self.command_label_widget = QtGui.QLabel()
      self.command_label_widget.setText("command to send: ")
      layout.addWidget(self.command_label_widget, 4, 0)

      self.enable_toggle = QtGui.QCheckBox("Enable Control")
      layout.addWidget(self.enable_toggle, 4, 1)
      self.enable_toggle.setChecked(False)
      self.enable_toggle.stateChanged.connect(self.enableToggleChanged)
      self.socket = None

      self.setLayout(layout)
      
      self.process_joystick_inputs = QtCore.QTimer()
      self.process_joystick_inputs.timeout.connect(self.processJoystickInput)
      self.process_joystick_inputs.start(1000.0/target_FPS)
      
      self.FPS = fps()
      
      self.button_lag = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] #used for latch behavior on joystick

   def enableToggleChanged(self):
      if self.enable_toggle.isChecked() and (self.controller is None):
         self.controller = WalkeraCommandThread()
         if (self.controller.s is not None): #likely not on network...
            self.controller.start()
            self.command_label_widget.setText(self.controller.getString() + " ...just opened!...")
         else:
            self.command_label_widget.setText(" controller failed to start! (wifi issues?)")
         self.manageSleepableWidget(self.controller)
         
      else:
         self.controller.shutdown()
         if (self.controller.s is not None): #likely not on network...
            self.controller.join()
         self.controller = None
         self.command_label_widget.setText("controller closed!...")
         
   def processJoystickInput(self): 
      try:
         tstamp, data = self.joystick_process_output_queue.get(False)
         
         # connect up buttons...
         # We're using the Logitech F310 USB Gamepad:
         # [LJ_LR, LJ_UD, RJ_LR, RJ_UD, X, A, B, Y, LB, RB, LT, RT, back, start, LJ_push, RJ_push]
         # [    0,     1,     2,     3, 4, 5, 6, 7,  8,  9, 10, 11,   12,    13,      14,      15]

         if data is not None:
            for i in range(len(self.button_lag)):
               if self.button_lag[i] > 0:
                  self.button_lag[i] -= 1
          
            if data[13]: # "start" (connected to enable toggle)
               if self.button_lag[13] == 0:
                  self.button_lag[13] = 10;
                  if self.enable_toggle.isChecked():
                     self.enable_toggle.setChecked(False)
                  else:
                     self.enable_toggle.setChecked(True)
            if data[8]: # "LB" (change to tab 0)
               self.gui.tabs.setCurrentIndex(0)
            if data[9]: # "RB" (change to tab 1)
               self.gui.tabs.setCurrentIndex(1)
         
         if self.controller is not None and data is not None:
            
            self.controller.setControlLevels(thrust=data[1], pitch=data[3], roll=data[2], yaw=data[0])

            try:
               self.thrust_queue.put((tstamp, -data[1]), False) #plot reversed
            except Queue.Full:
               pass

            try:
               self.pitch_queue.put((tstamp, data[3]), False)
            except Queue.Full:
               pass

            try:
               self.roll_queue.put((tstamp, data[2]), False)
            except Queue.Full:
               pass

            try:
               self.yaw_queue.put((tstamp, data[0]), False)
            except Queue.Full:
               pass
            
            self.FPS.update()
            #self.FPS.log()              

      except Queue.Empty:
         pass
   
class WalkeraGUI(QtGui.QWidget):
   def __init__(self):
      super(WalkeraGUI, self).__init__()

      self.objects_to_shutdown_at_quit = []

      self.tabs = QtGui.QTabWidget()
      
      tab1 = QtGui.QWidget()
      tab1_layout = QtGui.QGridLayout()
      
      self.vm = VideoManagerWidget()
      tab1_layout.addWidget(self.vm, 0, 0, 1, 3)
      self.objects_to_shutdown_at_quit.append(self.vm)
      
      #add a horizontal separator line
      hline_label = QtGui.QLabel()
      hline_label.setFrameStyle(QtGui.QFrame.HLine | QtGui.QFrame.Plain)
      hline_label.setLineWidth(2)
      tab1_layout.addWidget(hline_label, 1, 0, 1, 3)
      
      self.raw_widget = self.vm.createVideoProcessorWidget(IdentityProcess, process_label="Raw Video")
      tab1_layout.addWidget(self.raw_widget, 2, 0)
      self.lk_widget = self.vm.createVideoProcessorWidget(LKProcess, process_label="Optical Flow")
      tab1_layout.addWidget(self.lk_widget, 2, 1)
      self.fd_widget = self.vm.createVideoProcessorWidget(FaceDetectProcess, process_label="Face Detection")
      tab1_layout.addWidget(self.fd_widget, 2, 2)
      
      tab1.setLayout(tab1_layout)
      self.tabs.addTab(tab1, "CV")
      
      # 4-axis flight controls
      self.flight_control_widget = FlightControlWidget(gui=self)
      self.objects_to_shutdown_at_quit.append(self.flight_control_widget)
      self.tabs.addTab(self.flight_control_widget, "Flight Controls")
      
      # calibration tab
      tab3 = QtGui.QWidget()
      tab3_layout = QtGui.QGridLayout()
      
      self.calibration_video_widget = self.vm.createVideoProcessorWidget(IdentityProcess, process_label="Calibration Video", FPS_plot = False)
      tab3_layout.addWidget(self.calibration_video_widget, 0, 0, 1, 1, alignment=QtCore.Qt.AlignVCenter) #row, col, rspan, cspan
      
      self.calibration_snapshot_widget = self.vm.createVideoCalibrationWidget()
      tab3_layout.addWidget(self.calibration_snapshot_widget, 0, 1, 1, 1)
      
      tab3.setLayout(tab3_layout)
      self.tabs.addTab(tab3, "Calibration")
      
      #main window layout
      window_layout = QtGui.QHBoxLayout()
      window_layout.addWidget(self.tabs)
      
      self.setWindowTitle('Sene Cameras - QR-W100S')
      self.move(50,50)
      self.resize(1000, 550)
      self.setLayout(window_layout)
      
   def shutdown(self):
      for o in self.objects_to_shutdown_at_quit:
         o.shutdown()

if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   widget = WalkeraGUI()
   
   # raw video processing thread
   app.aboutToQuit.connect(widget.shutdown)

   widget.show()

   sys.exit(app.exec_())
   
