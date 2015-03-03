#!/usr/bin/env python

import sys
from PySide import QtGui, QtCore
import cv2
import time, datetime

import multiprocessing
import Queue #needed separately for the Empty exception

from vision.identity import IdentityProcess
from vision.lk import LKProcess
from vision.facedetect import FaceDetectProcess

from input.joystick import JoystickProcess
from input.video import SystemCamera1VideoProcess, WalkeraVideoProcess

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
         if o.isAwake():
            o.sleep()
   def wake(self):
      for o in self.managed_objects:
         if not o.isAwake():
            o.wake()
   def reset(self):
      for o in self.managed_objects:
         o.reset()
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
      
      self.camera_queue  = multiprocessing.Queue(maxsize=1)
      self.camera_process = SystemCamera1VideoProcess(self.camera_queue)
      self.camera_process.start()
   
      self.walkera_queue   = multiprocessing.Queue(maxsize=1)
      self.walkera_process = WalkeraVideoProcess(self.walkera_queue)
      self.walkera_process.start()
      
      #selector for video input type
      layout = QtGui.QHBoxLayout()
      self.src_type_group = QtGui.QButtonGroup()
      self.r0=QtGui.QRadioButton("Camera(1)")
      self.src_type_group.addButton(self.r0, 0)
      self.r0.clicked.connect(self.switchToCamera)
      self.r1=QtGui.QRadioButton("Walkera Wifi")
      self.src_type_group.addButton(self.r1, 1)
      self.r1.clicked.connect(self.switchToWalkera)
      self.r2=QtGui.QRadioButton("None")
      self.src_type_group.addButton(self.r2, 2)
      layout.addWidget(self.r0)
      layout.addWidget(self.r1)
      layout.addWidget(self.r2)
      self.setLayout(layout)
      
      self.get_images_t = QtCore.QTimer()
      self.get_images_t.timeout.connect(self.getImage)
      self.get_images_t.start(1000.0/target_FPS)
      
      self.get_images_FPS = fps()
      
      # default to cam1 video
      self.r0.setChecked(True)

   def createVideoProcessorWidget(self, process_class, process_label=""):
      new_vp_widget = VideoProcessorWidget(process_class, process_label)
      self.managed_processor_widgets.append(new_vp_widget)
      return new_vp_widget
   
   def getImage(self):
      if self.src_type_group.checkedId() == 2: #no video
         return
      
      if self.src_type_group.checkedId() == 0: #cam1
         try:
            tstamp, cv_img = self.camera_queue.get(False)
            self.get_images_FPS.update()
         except:
            return
      elif self.src_type_group.checkedId() == 1: #walkera
         try:
            tstamp, cv_img = self.walkera_queue.get(False)
            self.get_images_FPS.update()
         except:
            return
      
      for w in self.managed_processor_widgets:
         try:
            w.process_input_queue.put((tstamp, cv_img), False)
         except Queue.Full:
            pass
   
   def switchToCamera(self):
      for w in self.managed_processor_widgets:
         w.reset()
         
   def switchToWalkera(self):
      for w in self.managed_processor_widgets:
         w.reset()

   def shutdown(self):
      for w in self.managed_processor_widgets:
         w.shutdown()
      
      self.camera_process.shutdown()
      time.sleep(0.1)
      self.camera_process.terminate()
      
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
   def __init__(self, target_FPS = 60.0):
      self.process_class = JoystickProcess;
      super(FlightControlWidget, self).__init__(self.process_class)
      
      self.joystick_process_output_queue  = multiprocessing.Queue(maxsize=1)
      self.start( input_queue = None, output_queue = self.joystick_process_output_queue)

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
      self.thrust_widget.setYRange(-1, 1)
      self.thrust_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.thrust_widget, 1, 0)
      
      self.yaw_label = QtGui.QLabel()
      self.yaw_label.setText("Yaw")
      layout.addWidget(self.yaw_label, 2, 0)
      
      self.yaw_queue = Queue.Queue(maxsize=1)
      self.yaw_widget = TimeYQueuePlotWidget(self.yaw_queue)
      self.manageSleepableWidget(self.yaw_widget)
      self.yaw_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.yaw_widget.setYRange(-1, 1)
      self.yaw_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.yaw_widget, 3, 0)

      self.pitch_label = QtGui.QLabel()
      self.pitch_label.setText("Pitch")
      layout.addWidget(self.pitch_label, 0, 1)
      
      self.pitch_queue = Queue.Queue(maxsize=1)
      self.pitch_widget = TimeYQueuePlotWidget(self.pitch_queue)
      self.manageSleepableWidget(self.pitch_widget)
      self.pitch_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.pitch_widget.setYRange(-1, 1)
      self.pitch_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.pitch_widget, 1, 1)
      
      self.roll_label = QtGui.QLabel()
      self.roll_label.setText("Roll")
      layout.addWidget(self.roll_label, 2, 1)
      
      self.roll_queue = Queue.Queue(maxsize=1)
      self.roll_widget = TimeYQueuePlotWidget(self.roll_queue)
      self.manageSleepableWidget(self.roll_widget)
      self.roll_widget.setMaximumSize(self.plot_x_size,self.plot_y_size)
      self.roll_widget.setYRange(-1, 1)
      self.roll_widget.setLabel('left', 'Setpoint', units='au')
      layout.addWidget(self.roll_widget, 3, 1)

      self.setLayout(layout)
      
      self.get_joystick_inputs = QtCore.QTimer()
      self.get_joystick_inputs.timeout.connect(self.getJoystickInput)
      self.get_joystick_inputs.start(1000.0/target_FPS)
   
   def getJoystickInput(self):
      try:
         tstamp, data = self.joystick_process_output_queue.get(False)
         
         if (data is not None):
            try:
               self.thrust_queue.put((tstamp, data[1]), False)
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
         
      except Queue.Empty:
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
      
      self.raw_widget = self.vm.createVideoProcessorWidget(IdentityProcess, process_label="Raw Video")
      tab1_layout.addWidget(self.raw_widget, 1, 0)
      self.lk_widget = self.vm.createVideoProcessorWidget(LKProcess, process_label="Optical Flow")
      tab1_layout.addWidget(self.lk_widget, 1, 1)
      self.fd_widget = self.vm.createVideoProcessorWidget(FaceDetectProcess, process_label="Face Detection")
      tab1_layout.addWidget(self.fd_widget, 1, 2)
      
      tab1.setLayout(tab1_layout)
      tabs.addTab(tab1, "CV")
      
      # 4-axis flight controls
      self.flight_control_widget = FlightControlWidget()
      self.objects_to_shutdown_at_quit.append(self.flight_control_widget)
      tabs.addTab(self.flight_control_widget, "Flight Controls")
      
      # Walkera QR-W100S
      tab3 = QtGui.QWidget()
      tab3_layout = QtGui.QGridLayout()
      tab3_instructions = QtGui.QLabel()
      tab3_instructions.setText("Connect to the Walkera WiFi connection!")
      tab3_layout.addWidget(tab3_instructions, 0, 0)
      tab3.setLayout(tab3_layout)
      tabs.addTab(tab3, "QR-W100S")
      
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

if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   widget = WalkeraGUI()
   
   # raw video processing thread
   app.aboutToQuit.connect(widget.shutdown)

   widget.show()

   sys.exit(app.exec_())
   
