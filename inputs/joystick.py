import pygame

class Joystick:
    def __init__(self):
        pygame.init()
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

    
            
