import Tkinter as tk
import tkFileDialog
import os
import threading
import time
class Interface():
    def __init__(self):
        self.recording = False
        self.images = []
        self.root = tk.Tk()
        self.root.bind('<Escape>', lambda e: self.set_quit_flag())  
        self.root.bind("<KeyRelease-s>", lambda e: self.askdirectory())  
        self.root.bind("<KeyRelease-r>", lambda e: self.startRecording())
        setattr(self.root, 'quit_flag', False)
        self.root.protocol('WM_DELETE_WINDOW', self.set_quit_flag)
        self.recordButton = tk.Button(self.root, text="Record", command= lambda: self.startRecording())
        self.saveButton = tk.Button(self.root, text="Set Directory", command= lambda: self.askdirectory())
        self.recordButton.pack()
        self.saveButton.pack()
        self.x = 0
        
        self.base_directory = 'video_' 
        
    def set_quit_flag(self):
        if self.root.quit_flag == False:
            self.root.quit_flag = True
            self.root.destroy()
        
    def askdirectory(self):
        # defining options for opening a directory
        dir_opt = options = {}
        options['initialdir'] = '.'#os.path.dirname(os.path.realpath(__file__))
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'This is a title'
        self.base_directory = tkFileDialog.askdirectory(**dir_opt) + ''
        if not os.path.exists(self.base_directory): os.makedirs(self.base_directory)         
        """Returns a selected directoryname."""
        #if self.recording == True:
        #    print 'saving'
            # self.recordButton.config(relief=SUNKEN)
            # print self.recordButton.relief()
        #    self.recording = False
        #    directory = tkFileDialog.askdirectory(**dir_opt) + '/arbitrary'
        #    if directory != '/arbitrary' and len(self.images) > 0:
        #        print "Location of folder:", directory

        #        f = open(directory+'/image.jpeg','w')
        #        for x in range(len(self.images)):
        #            cv2.imwrite(directory+'/image%s.jpg' % x,self.images[x])

    def record(self, frame):
        
        dump = open(self.directory+'/image%s.jpg' % self.x,'w')        
        self.x += 1
        dump.write(frame)
            
    def startRecording(self):
        
        self.recording = not self.recording
        if not self.recording:
            print "stopped"
        else:
            self.directory = self.base_directory + '/v_'+time.strftime('%Y-%m-%d-%H-%M-%S')
            os.makedirs(self.directory)                
            print "recording"
        
    def startThread(self):
        self.myThread = threading.Thread(target=self.root.mainloop)
        self.myThread.start()


if __name__ == "__main__":
    ui = Interface()
    ui.startThread()