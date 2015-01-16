import Tkinter as tk
import tkFileDialog
import os
import threading

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
        self.saveButton = tk.Button(self.root, text="Save", command= lambda: self.askdirectory())
        self.recordButton.pack()
        self.saveButton.pack()

    def set_quit_flag(self):
        if self.root.quit_flag == False:
            self.root.quit_flag = True
            self.root.destroy()
        
    def askdirectory(self):
        # defining options for opening a directory
        dir_opt = options = {}
        options['initialdir'] = os.path.dirname(os.path.realpath(__file__))
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'This is a title'

        """Returns a selected directoryname."""
        if self.recording == True:
            print 'saving'
            # self.recordButton.config(relief=SUNKEN)
            # print self.recordButton.relief()
            self.recording = False
            directory = tkFileDialog.askdirectory(**dir_opt) + '/arbitrary'
            if directory != '/arbitrary' and len(self.images) > 0:
                print "Location of folder:", directory
                if not os.path.exists(directory): os.makedirs(directory)
                f = open(directory+'/image.jpeg','w')
                for x in range(len(self.images)):
                    cv2.imwrite(directory+'/image%s.jpg' % x,self.images[x])

    def startRecording(self):
        self.recording
        if self.recording == False:
            print "recording"
            self.recording = True

    def startThread(self):
        self.myThread = threading.Thread(target=self.root.mainloop())
        self.myThread.start()


if __name__ == "__main__":
    ui = Interface()
    ui.startThread()