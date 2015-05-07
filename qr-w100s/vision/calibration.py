#!/usr/bin/env python
import cv2
import numpy as np
import sys

'''
based on http://docs.opencv.org/doc/tutorials/calib3d/camera_calibration/camera_calibration.html#cameracalibrationopencv
'''

def printnow(string):
   print string
   sys.stdout.flush()

class CameraCalibrator():
   def __init__(self):
      self.points_per_row = 9
      self.points_per_column = 7
      self.board_square_size_mm = 25.4 # The size of a square in millimeters
      
   def findCorners(self, cv_img):
      retval, corners = cv2.findChessboardCorners(cv_img, (self.points_per_row, self.points_per_column))
      if retval:
         # improve accuracy (might need to be tuned based on image size...
         gray = cv2.cvtColor(cv_img.copy(), cv2.COLOR_BGR2GRAY)
         cv2.cornerSubPix(gray, corners, (2,2), (-1,-1), (cv2.cv.CV_TERMCRIT_ITER | cv2.cv.CV_TERMCRIT_EPS, 20, 0.001))
      return corners

   def drawCorners(self, cv_img, corners):
      copy = cv_img.copy()
      cv2.drawChessboardCorners(copy, (self.points_per_row, self.points_per_column), corners, True)
      return copy
         
   def calibrate(self, image_points, image_size=(320,240)):
      objp = np.zeros((self.points_per_column*self.points_per_row,3), np.float32)
      objp[:,:2] = np.mgrid[0:self.points_per_row, 0:self.points_per_column].T.reshape(-1,2)
      objp *= self.board_square_size_mm
      object_points = []
      for i in range(len(image_points)):
         object_points.append(objp) # load up the object points with a clean grid

      try:
         retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(object_points, image_points, image_size)
         
         # calculate how good the fit is..
         total_error_squared = 0
         total_num_points = 0
         for i in range(len(object_points)):
            projected_image_points, jacobian = cv2.projectPoints(object_points[i], rvecs[i], tvecs[i], cameraMatrix, distCoeffs)
            
            error_squared = 0
            num_points = 0
            for j in range(len(image_points[i])):
               dx = (image_points[i][j][0][0] - projected_image_points[j][0][0])
               dy = (image_points[i][j][0][1] - projected_image_points[j][0][1])
               error_squared += dx*dx + dy*dy
               num_points += 1
            printnow("error[%d]=%f" % ( i, np.sqrt(error_squared/num_points) ) )
            total_error_squared += error_squared
            total_num_points += num_points
            
         printnow("average error=%f" % np.sqrt(total_error_squared/total_num_points) )
         
         printnow((len(image_points), cameraMatrix[0,0], cameraMatrix[1,1], cameraMatrix[0,2], cameraMatrix[1,2], distCoeffs[0][0], distCoeffs[0][1], distCoeffs[0][2], distCoeffs[0][3], distCoeffs[0][4]))
         
         return cameraMatrix, distCoeffs
      
      except Exception, e:
         pass
 
if __name__ == '__main__':
   calibrator = CameraCalibrator()
   print "no unit test"
