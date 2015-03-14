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
      
      #from previous calibrations... Lenovo webcam
      self.camera_matrix = [[ 336.77949873 ,   0.         ,   139.55976082],
                           [    0.         , 337.41454138 ,    91.37560863],
                           [    0.         ,   0.         ,     1.        ]]
      self.distortion_coeffs =  [-0.03933975,  0.10248906, -0.02188526, -0.0065168,  -0.12065639]
      
      ''' again...
      [[ 317.55744649    0.          151.38193851]
      [   0.          319.7940645   118.97117154]
      [   0.            0.            1.        ]]
     [[-0.07489437  0.32156917 -0.00979001  0.00162971 -0.82121261]]
     
     [[ 320.72490556    0.          159.21049723]
      [   0.          323.14303127  113.12560677]
      [   0.            0.            1.        ]]
      
      [[  99.96513067    0.          159.49998559]
      [   0.          101.88542444  119.50000816]
      [   0.            0.            1.        ]]
      
      '''

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
         object_points.append(objp)
      try:
         retval, cameraMatrix, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(object_points, image_points, image_size)
         printnow((len(image_points), cameraMatrix[0,0], cameraMatrix[1,1], cameraMatrix[0,2], cameraMatrix[1,2], distCoeffs[0][0], distCoeffs[0][1], distCoeffs[0][2], distCoeffs[0][3], distCoeffs[0][4]))
      except Exception, e:
         pass
      #consider passing parameter string back?
 
if __name__ == '__main__':
   calibrator = CameraCalibrator()

   '''

   def calibrate(self):

      cameraMatrix = Mat::eye(3, 3, CV_64F);
      if( s.flag & CV_CALIB_FIX_ASPECT_RATIO )
         cameraMatrix.at<double>(0,0) = 1.0;
      
      distCoeffs = Mat::zeros(8, 1, CV_64F);
      vector<vector<Point3f> > objectPoints(1);
      
      corners.clear();



    //Find intrinsic and extrinsic camera parameters
    double rms = calibrateCamera(objectPoints, imagePoints, imageSize, cameraMatrix,
                                 distCoeffs, rvecs, tvecs, s.flag|CV_CALIB_FIX_K4|CV_CALIB_FIX_K5);

    cout << "Re-projection error reported by calibrateCamera: "<< rms << endl;

    bool ok = checkRange(cameraMatrix) && checkRange(distCoeffs);

    totalAvgErr = computeReprojectionErrors(objectPoints, imagePoints,
                                             rvecs, tvecs, cameraMatrix, distCoeffs, reprojErrs);

    return ok;



          if( runCalibrationAndSave(s, imageSize,  cameraMatrix, distCoeffs, imagePoints))
              mode = CALIBRATED;
          else
              mode = DETECTION;
      }

        imageSize = view.size();  // Format input image.


        vector<Point2f> pointBuf;

        bool found;
        

        

        //----------------------------- Output Text ------------------------------------------------
        string msg = (mode == CAPTURING) ? "100/100" :
                      mode == CALIBRATED ? "Calibrated" : "Press 'g' to start";
        int baseLine = 0;
        Size textSize = getTextSize(msg, 1, 1, 1, &baseLine);
        Point textOrigin(view.cols - 2*textSize.width - 10, view.rows - 2*baseLine - 10);

        if( mode == CAPTURING )
        {
            if(s.showUndistorsed)
                msg = format( "%d/%d Undist", (int)imagePoints.size(), s.nrFrames );
            else
                msg = format( "%d/%d", (int)imagePoints.size(), s.nrFrames );
        }

        putText( view, msg, textOrigin, 1, 1, mode == CALIBRATED ?  GREEN : RED);

        if( blinkOutput )
            bitwise_not(view, view);

        //------------------------- Video capture  output  undistorted ------------------------------
        if( mode == CALIBRATED && s.showUndistorsed )
        {
            Mat temp = view.clone();
            undistort(temp, view, cameraMatrix, distCoeffs);
        }

        //------------------------------ Show image and check for input commands -------------------
        imshow("Image View", view);
        char key = (char)waitKey(s.inputCapture.isOpened() ? 50 : s.delay);

        if( key  == ESC_KEY )
            break;

        if( key == 'u' && mode == CALIBRATED )
           s.showUndistorsed = !s.showUndistorsed;

        if( s.inputCapture.isOpened() && key == 'g' )
        {
            mode = CAPTURING;
            imagePoints.clear();
        }
    }

    // -----------------------Show the undistorted image for the image list ------------------------
    if( s.inputType == Settings::IMAGE_LIST && s.showUndistorsed )
    {
        Mat view, rview, map1, map2;
        initUndistortRectifyMap(cameraMatrix, distCoeffs, Mat(),
            getOptimalNewCameraMatrix(cameraMatrix, distCoeffs, imageSize, 1, imageSize, 0),
            imageSize, CV_16SC2, map1, map2);

        for(int i = 0; i < (int)s.imageList.size(); i++ )
        {
            view = imread(s.imageList[i], 1);
            if(view.empty())
                continue;
            remap(view, rview, map1, map2, INTER_LINEAR);
            imshow("Image View", rview);
            char c = (char)waitKey();
            if( c  == ESC_KEY || c == 'q' || c == 'Q' )
                break;
        }
    }


    return 0;
   


static double computeReprojectionErrors( const vector<vector<Point3f> >& objectPoints,
                                         const vector<vector<Point2f> >& imagePoints,
                                         const vector<Mat>& rvecs, const vector<Mat>& tvecs,
                                         const Mat& cameraMatrix , const Mat& distCoeffs,
                                         vector<float>& perViewErrors)
{
    vector<Point2f> imagePoints2;
    int i, totalPoints = 0;
    double totalErr = 0, err;
    perViewErrors.resize(objectPoints.size());

    for( i = 0; i < (int)objectPoints.size(); ++i )
    {
        projectPoints( Mat(objectPoints[i]), rvecs[i], tvecs[i], cameraMatrix,
                       distCoeffs, imagePoints2);
        err = norm(Mat(imagePoints[i]), Mat(imagePoints2), CV_L2);

        int n = (int)objectPoints[i].size();
        perViewErrors[i] = (float) std::sqrt(err*err/n);
        totalErr        += err*err;
        totalPoints     += n;
    }

    return std::sqrt(totalErr/totalPoints);
}

'''
