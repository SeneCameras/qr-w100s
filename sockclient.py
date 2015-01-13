import socket
import time
import re 

reqstr = open('reqstr').read()
def readframes(sock, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True
    state = 0
    ts = 0
    while data:
        try:


            data = sock.recv(recv_buffer)
            buffer += data
        except socket.error, e:
            print e
        while buffer.find(delim) != -1:
            line, buffer = buffer.split("\n", 1)
            if state==0:
                if line[0:20] == "--boundarydonotcross":
                    state = 1
            elif state==1:
                print line.split(":")
                state = 2
            elif state==2:
                print line
                datalength = int(line.split(":")[1][1:-1])
                state = 3
                print "datalen", datalength
                #print buffer
            elif state==3:
                state = 4
                
                timestamp = float(line.split(":")[1][1:-1])
                print "timestamp:", timestamp
                print "lag", timestamp - ts, 1/( timestamp - ts)
                ts = timestamp
            else:
                while(len(buffer) < datalength):
                    bytes_remaining = datalength - len(buffer)
                    data = sock.recv(bytes_remaining)
                    buffer += data
                state = 0
                yield buffer
    return

if __name__ == "__main__":
    HOST, PORT = "192.168.10.1", 8080
    # f = open('dump','w')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.setblocking(False)
    sock.send(reqstr)
    size = 0
    a = time.time()
    n = 1
    avg = 0
    x = 0
    for frame in readframes(sock):
        t = time.time()
        fps = 1/(t-a)
        print "frame len: ", len(frame)
        print (fps, avg)
        a = t
        x = x+1
        if (x==120):
            
            x = 0
            print frame
    # recvd = ''
    
    
    # while 1:
        # data = sock.recv(18880)
        # size+=len(data)
        # print size
        # if not data: 
            # break
        # f.write(data)
        
        
 # 
 
