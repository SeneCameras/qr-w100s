import Tkinter as tk
import tkFileDialog
import os
import json
from threading import Thread
import time
from videoplayer import VideoPlayer
import cv2

class Interface(Thread):
    def __init__(self, video, control, joystick):
        Thread.__init__(self)
        self.video = video
        self.control = control
        self.joystick = joystick
        self.video_player = None
        self.recording = False
        self.images = []
        self.root = tk.Tk()
        self.root.bind('<Escape>', lambda e: self.set_quit_flag())  
        self.root.bind("<KeyRelease-s>", lambda e: self.askdirectory())  
        self.root.bind("<KeyRelease-r>", lambda e: self.startRecording())
        setattr(self.root, 'quit_flag', False)
        self.root.protocol('WM_DELETE_WINDOW', self.set_quit_flag)
        self.recordButton = tk.Button(self.root, text="Record", command= lambda: self.startRecording())
        self.setdirButton = tk.Button(self.root, text="Set Directory", command= lambda: self.askdirectory())
        self.startControl = tk.Button(self.root, text="Connect to Control", command= lambda: self.connect_control())
        self.startVideo = tk.Button(self.root, text="Connect to Video", command= lambda: self.connect_video())
        self.startJoyStick = tk.Button(self.root, text="Connect to Joystick", command= lambda: self.connect_joystick())
        self.startVideoProcess = tk.Button(self.root, text="Start Video Process", command= lambda: self.start_video_process())
        self.startAll = tk.Button(self.root, text="Start All", command= lambda: self.start_all())
        self.loadVideo = tk.Button(self.root, text="Load Video", command= lambda: self.load_video())
        
        self.setdirButton.pack()
        self.recordButton.pack()
        self.startControl.pack()
        self.startVideo.pack()
        self.startJoyStick.pack()
        self.startVideoProcess.pack()
        self.startAll.pack()
        self.loadVideo.pack()
        
        self.x = 0
        
        self.base_directory = 'video_' 
    def attach_video_process(self, vp):
        self.video_process = vp
        
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
        fn = 'im%s.jpg' % self.x
        if (self.x > 0):            
            self.manifest.write(",\""+fn+"\"")
        else:
            self.manifest.write("\""+fn+"\"")
        #dump = open(self.directory+'/'+fn,'w')        
        cv2.imwrite(self.directory+'/'+fn,frame)
        self.x += 1
        #dump.write(frame)
            
    def startRecording(self):
        

        if self.recording:
            self.manifest.write(']')
            self.manifest.close()
            self.recording = False
            print "stopped"
        else:
            self.x = 0
            self.directory = self.base_directory + '/v_'+time.strftime('%Y-%m-%d-%H-%M-%S')
            os.makedirs(self.directory)  
            self.manifest = open(self.directory+'/manifest.json','w')
            self.manifest.write('[')
            self.recording = True
            print "recording"
        
    def run(self):
        self.root.mainloop()

    def connect_control(self):    
        self.control.start()
        
    def connect_video(self):
        self.video_process.vid = self.video
        
        if self.video_player != None:
            del self.video_player
        #self.video.start()
        
    def connect_joystick(self):
        self.joystick.start()
        
    def start_video_process(self):
        self.video_process.start()
        
    def start_all(self):
        self.connect_control()
        self.connect_video()
        self.connect_joystick()
        
        self.start_video_process()
    
    def load_video(self):
        dir_opt = options = {}
        options['initialdir'] = '.'#os.path.dirname(os.path.realpath(__file__))
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'This is a title'
        self.base_directory = tkFileDialog.askdirectory(**dir_opt)
        try:
            manifest = open(self.base_directory+"/manifest.json")
            file_list = json.loads(manifest.read())
            self.video_player = VideoPlayer(self.base_directory, file_list)
            self.video_process.vid = self.video_player
        except Exception, e:
            print e
            pass
        
if __name__ == "__main__":
    ui = Interface()
    ui.startThread()