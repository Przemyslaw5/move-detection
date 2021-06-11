import threading
import cv2
import time
from framer import Framer
from camera import Camera
import imutils
from datetime import datetime
import ffmpeg
import numpy as np
import subprocess

class MoveDetector(Framer):
    thread = None  # background thread that reads frames from move detector
    frame = None  # current frame is stored here by background thread
    width = None
    height = None
    email_sending = None
    recording_time = None
    min_area = None
    
    def __init__(self):
        """Start the background move_detector thread if it isn't running yet."""
        if MoveDetector.thread is None:
            # start background frame thread
            MoveDetector.thread = threading.Thread(target=self._thread, args=(Camera(),))
            MoveDetector.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)
                
    @staticmethod
    def set_width(cls, value):
        cls.width = value
        
    @staticmethod
    def set_height(cls, value):
        cls.height = value
        
    @staticmethod
    def set_email_sending(cls, value):
        cls.email_sending = value
        
    @staticmethod
    def set_recording_time(cls, value):
        cls.recording_time = value
        
    @staticmethod
    def set_min_area(cls, value):
        cls.min_area = value

    def get_frame(self):
        """Return the current move_detector frame."""
        return MoveDetector.frame


    @classmethod
    def _thread(cls, camera: Camera):
        """MoveDetection background thread."""
        print('Starting move detection thread.')
        
        # initialize the first frame in the video stream
        firstFrame = None
        # loop over the frames of the video
        frames_to_write = 0
        video_writer = None

        size = (cls.width, cls.height)
        
        # set fourcc, framerate
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        framerate = 20
        
        while True:
            frame = camera.get_frame()
            clean_frame = frame
            text = "Unoccupied"
            
            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # if the first frame is None, initialize it
            if firstFrame is None:
                firstFrame = gray
                continue
            
            # compute the absolute difference between the current frame and first frame
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # dilate the thresholded image to fill in holes, then find contours on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            
            # loop over the contours
            for c in cnts:
                
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < cls.min_area:
                    continue
                
                # compute the bounding box for the contour, draw it on the frame, and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Occupied"
                
                # calculate minimum number frames which are write to file
                frames_to_write = cls.recording_time*framerate
                
            # draw the text and timestamp on the frame
            cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            
            # We update the fame which is positioned on the site
            MoveDetector.frame = frame
            
            # If we have frames to write we are start recording
            if frames_to_write > 0 :
                if video_writer == None :
                    time = datetime.now()
                    output_filename = f'static/videos/{time.strftime("%y_%m_%d_%H_%M_%S")}'
                    video_writer = cv2.VideoWriter(output_filename + ".avi", fourcc, framerate, size)
                    
                # In video we have save clean frame without any contour
                video_writer.write(clean_frame)
                
                frames_to_write -= 1
                
                # If we and create the video we have to convert file from avi to mp4
                if frames_to_write <= 0:
                    video_writer.release()
                    subprocess.Popen(['python3', 'convert.py', '-f', output_filename, '-s', str(cls.email_sending)])
                    video_writer = None