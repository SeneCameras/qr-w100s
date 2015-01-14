import Tkinter as tk
import cv2
# from PIL import Image, ImageTk
from walkera.video2 import Video

root = tk.Tk()
root.bind('<Escape>', lambda e: root.quit())


v = Video()
v.setClassifier("haarcascade_frontalface_alt2.xml")
v.startThread()
v.detectFaces = True


# def show_frame():
#     _, frame = cap.read()
#     frame = cv2.flip(frame, 1)
#     cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
#     img = Image.fromarray(cv2image)
#     imgtk = ImageTk.PhotoImage(image=img)
#     lmain.imgtk = imgtk
#     lmain.configure(image=imgtk)
#     lmain.after(10, show_frame)

# show_frame()
root.mainloop()