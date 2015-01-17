import pygame
from threading import Thread

class Joystick(Thread):
    def __init__(self):
        pygame.init()
        Thread.__init__(self)
        self.j = pygame.joystick.Joystick(0)
        self.j.init()
        print 'Found', self.j.get_name()

    def get(self):
        out = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        it = 0 #iterator
        pygame.event.pump()
        
        #Read input from the two joysticks       
        for i in range(0, self.j.get_numaxes()):
            out[it] = self.j.get_axis(i)
            it+=1
        #Read input from buttons
        for i in range(0, self.j.get_numbuttons()):
            out[it] = self.j.get_button(i)
            it+=1
            
        return out

    def test(self):
        while True:
            print self.get()

    
    def attach_control(self,c):
        self.c = c
        
    def run(self):
        while 1:
            cntrlrdata = self.get()
            
            if (cntrlrdata[4] == 1):
                
                self.c.stop = False
            if (cntrlrdata[5] == 1):
                
                self.c.stop = True
            
            #print "Axis 0", cntrlrdata[0], "Axis 1", cntrlrdata[1], "Axis 2", cntrlrdata[2], "Axis 3", cntrlrdata[3]
            if (not self.c.stop):
                self.c.setThrottle(int((1 - cntrlrdata[1])*((0x05dc-0x02bf)>>1)) + 0x02bf) #Throttle Range 02bf to 05dc
                self.c.setRotation(int((1 - cntrlrdata[0])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
                self.c.setElev(int((1 - cntrlrdata[3])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
                self.c.setAile(int((1 - cntrlrdata[2])*((0x0640-0x025b)>>1)) + 0x025b) #025b to 0640
            else:
                pass
                #print cntrlrdata
    
