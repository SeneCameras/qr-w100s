#!/usr/bin/env python

import pygame
import sys

import multiprocessing
import Queue #needed separately for the Empty exception
import time, datetime

class JoystickProcess(multiprocessing.Process):
   def __init__(self, outputqueue):
      multiprocessing.Process.__init__(self)
      self.outputqueue = outputqueue
      self.exit = multiprocessing.Event()
      self.sleeping = multiprocessing.Event()

   def shutdown(self):
      self.exit.set()
      
   def sleep(self):
      self.sleeping.set()
      
   def wake(self):
      self.sleeping.clear()
      
   def run(self):
      
      pygame.init()
      self.j = pygame.joystick.Joystick(0)
      self.j.init()

      print 'Found: ', self.j.get_name()
      sys.stdout.flush()
      
      while not self.exit.is_set():
         
         if self.sleeping.is_set():
            time.sleep(0.1)
            continue
         
         data = self.get()
         
         if (data is not None):
            tstamp = datetime.datetime.now()
            try:
               self.outputqueue.put((tstamp, data), False)
            except Queue.Full:
               continue

   def get(self):
        out = []
        pygame.event.pump()
        
        #Read input from joysticks       
        for i in range(self.j.get_numaxes()):
            out.append(self.j.get_axis(i))
            
        #Read input from buttons
        for i in range(self.j.get_numbuttons()):
            out.append(self.j.get_button(i))
            
        return out
      
if __name__ == '__main__':
   
   q = multiprocessing.Queue(maxsize=1)
   j = JoystickProcess(q)
   j.start()

   while(1):
      try:
         tstamp, data = q.get(False)
         print tstamp, data
         sys.stdout.flush()
      except Queue.Empty:
         pass
