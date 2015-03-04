#!/usr/bin/env python

from PySide import QtGui, QtCore

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    
from input.video import VideoTestWidget, WalkeraVideoProcess

import socket
import binascii
import time
import sys
import threading

class WalkeraCommandThread(threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
  
      self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1) #disable Nagle          
      self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)   #disable kernel buffer
      self.s.settimeout(0.5) #don't wait if we're not connected to a Walkera network
      try:
         self.s.connect(("192.168.10.1", 2001))
      except Exception, e:
         if ("%s"%e).find("timed out") == 0:
            print "[Socket Connection Timeout] You may not be connected to the Walkera WiFi network..."
            sys.stdout.flush()
            self.s = None
            return
         
      self.s.setblocking(0)
      
      self.stopping = threading.Event()
      
      self.FPS = 35
      
      self.data  = bytearray(18)
      self.zero()
      
      print "*****************  Walkera Control Thread Initialized  *****************"
      sys.stdout.flush()

   def zero(self):
      self.switch   = 0x61
      self.thrust   = 0x02bf #min value
      self.yaw      = 0x044a
      self.pitch    = 0x044a
      self.roll     = 0x044a
      self.update()
      
   def update(self):
      self.data[0] = self.switch #enable code
      self.data[1] = self.thrust >> 8
      self.data[2] = self.thrust & 0xff
      self.data[3] = self.yaw >> 8
      self.data[4] = self.yaw & 0xff
      self.data[5] = self.pitch >> 8
      self.data[6] = self.pitch & 0xff
      self.data[7] = self.roll >> 8
      self.data[8] = self.roll & 0xff
      self.data[9] = self.roll >> 8
      self.data[10] = self.roll & 0xff
      self.data[11] = self.thrust >> 8
      self.data[12] = self.thrust & 0xff
      self.data[13] = self.yaw >> 8
      self.data[14] = self.yaw & 0xff
      self.data[15] = self.pitch >> 8
      self.data[16] = self.pitch & 0xff
      self.data[17] = sum(self.data[0:17]) & 0xFF
      
   def getString(self):
      return binascii.hexlify(self.data)

   def setControlLevels(self, thrust=0.0, pitch=0.0, roll=0.0, yaw=0.0):
      self.thrust = (int((1 - thrust) * ((0x05dc-0x02bf)>>1)) + 0x02bf)
      self.pitch  = (int((1 - pitch ) * ((0x0640-0x025b)>>1)) + 0x025b)
      self.roll   = (int((1 - roll  ) * ((0x0640-0x025b)>>1)) + 0x025b)
      self.yaw    = (int((1 - yaw   ) * ((0x0640-0x025b)>>1)) + 0x025b)

   def run(self):
      
      self.zero()
      self.s.send(self.data) #first sent values must be min thrust
      
      while not self.stopping.is_set():
         self.update()
         self.s.send(self.data)
         time.sleep(1.0/self.FPS) # breaks over 60 FPS based on testing...

      print "*****************  Walkera Control Thread Now Stopped  *****************"
      sys.stdout.flush()
      
      self.zero()
      self.s.send(self.data)
      
      time.sleep(0.01)
      
      self.s.close()
      
   def shutdown(self):
      self.stopping.set()
      
   def sleep(self):
      pass
   def wake(self):
      pass
   def reset(self):
      pass
 
 
class TestDriver():
   def __init__(self, command_thread):
      self.wct = command_thread
      self.FPS = self.wct.FPS
      print "now sending at %d FPS" % self.FPS
      sys.stdout.flush()
   def pulse(self):
      print "pulsing now"
      sys.stdout.flush()
      self.wct.setControlLevels(thrust=-1.0, pitch=0.0, roll=0.0, yaw=0.0)
      time.sleep(0.1)
      self.wct.setControlLevels(thrust= 1.0, pitch=0.0, roll=0.0, yaw=0.0)
      time.sleep(0.1)
   def boostFPS(self):
      self.FPS += 5
      self.wct.FPS = self.FPS
      print "now sending at %d FPS" % self.FPS
      sys.stdout.flush()
      
if __name__ == '__main__':
   app = QtGui.QApplication(sys.argv)
   
   widget     = VideoTestWidget(WalkeraVideoProcess)
   controller = WalkeraCommandThread()
   if (controller.s is not None):
      driver     = TestDriver(controller)
   
      controller.start()
      widget.managed_objects.append(controller)
      
      t1 = QtCore.QTimer()
      t1.timeout.connect(driver.pulse)
      t1.start(1000.0/0.7)
      
      t2 = QtCore.QTimer()
      t2.timeout.connect(driver.boostFPS)
      t2.start(1000.0/0.2)
   
   app.aboutToQuit.connect(widget.shutdown)
   
   widget.show()
   
   sys.exit(app.exec_())
   
   
   

   