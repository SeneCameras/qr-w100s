import SocketServer
import time
import os
class MyTCPHandler(SocketServer.StreamRequestHandler ):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024)
        #open('reqstr','w').write(self.data)
        print "{} wrote:".format(self.client_address[0])
        print self.data
        header = open("header.txt")
        self.wfile.write(header.read(1024))
        frame = open("frame.txt")
        fs = os.path.getsize('frame.txt')
        data_not_empty = True
        while 1:

            txt = frame.read(fs)
            
            self.wfile.write(txt)
            frame.seek(0)
            time.sleep(.03)
        # just send back the same data, but upper-cased
        #self.request.sendall(self.data.upper())

if __name__ == "__main__":
    HOST, PORT = "192.168.10.1", 8080

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    print "server started"
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()