import urllib2

class Video:
    def __init__(self):
        self.password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()                
        self.top_level_url = "http://192.168.10.1:8080"
       
    def frames(self, recv_buffer=4096, delim='\n'):
        buffer = ''
        data = True
        self.reading = True
        self.state = 0
        ts = 0
        self.password_mgr.add_password(None, self.top_level_url, 'admin', 'admin123')
        self.handler = urllib2.HTTPBasicAuthHandler(self.password_mgr)
        self.opener = urllib2.build_opener(self.handler)
        self.opener.open("http://192.168.10.1:8080/?action=stream")
        urllib2.install_opener(self.opener)
        print 'opening video url'        
        self.resp = urllib2.urlopen("http://192.168.10.1:8080/?action=stream")            
        
        print ' in readframes'
        while data and self.reading:
            #print 'recv buffer'
            data = self.resp.read(recv_buffer)
            #print 'data'
            buffer += data
            while buffer.find(delim) != -1:
                line, buffer = buffer.split("\n", 1)
                if self.state==0:
                    if line[0:20] == "--boundarydonotcross":
                        self.state = 1
                elif self.state==1:
                    # print line.split(":")
                    self.state = 2
                elif self.state==2:
                    #print line
                    datalength = int(line.split(":")[1][1:-1])
                    self.state = 3
 #                   print "datalen", datalength
                    #print buffer
                elif self.state==3:
                    self.state = 4
                    
                    timestamp = float(line.split(":")[1][1:-1])
#                    print "timestamp:", timestamp
                    #print "lag", timestamp - ts, 1/( timestamp - ts)
                    ts = timestamp
                else:
                    while(len(buffer) < datalength):
                        bytes_remaining = datalength - len(buffer)
                        data = self.resp.read(bytes_remaining)
                        buffer += data

                    self.state = 0
                    
                    yield buffer
        quit(0)
    

