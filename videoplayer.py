import os



class VideoPlayer:
    def __init__(self, basedir, filelist):
        self.basedir = basedir
        self.filelist = filelist
        self.current = 0
        self.length = len(filelist)
        
    def frames(self):
        
        print 'opening video player'        
        while 1:
            file = self.basedir + "/" + self.filelist[self.current]
#print "opening file: ", file
            self.resp = open(file, "rb")
            data = self.resp.read()
            self.current = self.current + 1
            if self.current >= self.length:
                self.current = 0
            yield data

