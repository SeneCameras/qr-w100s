import socket


reqstr = open('reqstr').read()

if __name__ == "__main__":
    HOST, PORT = "192.168.10.1", 8080
    f = open('dump','w')
    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(reqstr)
    size = 0
    recvd = ''
    while 1:
        data = sock.recv(18880)
        size+=len(data)
        print size
        if not data: 
            break
        f.write(data)
 