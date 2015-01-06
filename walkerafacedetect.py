import cv2
import numpy as np
import urllib

stream=urllib.urlopen('http://192.168.10.1:8080/?action=stream')
bytes=''
# face detection classifiers
frontalclassifier = cv2.CascadeClassifier("haarcascade_frontalface_alt2.xml")     # frontal face pattern detection
profileclassifier = cv2.CascadeClassifier("haarcascade_profileface.xml")      # side face pattern detection
DOWNSCALE = 4


while True:
    bytes+=stream.read(1080)
    # b = bytes.find('--markmarkmark')
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        jpg = bytes[a:b+2]
        bytes= bytes[b+2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.CV_LOAD_IMAGE_GRAYSCALE)
        if frame!= None:
            # detect faces and draw bounding boxes
            minisize = (frame.shape[1]/DOWNSCALE,frame.shape[0]/DOWNSCALE)
            miniframe = cv2.resize(frame, minisize)
            frontalfaces = frontalclassifier.detectMultiScale(miniframe)
            profilefaces = profileclassifier.detectMultiScale(miniframe)
            for f in frontalfaces:
                x, y, w, h = [ v*DOWNSCALE for v in f ]
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255))
            for f in profilefaces:
                x, y, w, h = [ v*DOWNSCALE for v in f ]
                cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0))
            cv2.imshow('authenticated cam',frame)
        if cv2.waitKey(1) ==27:
            exit(0)   
