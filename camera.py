import threading
import cv2
import time
from framer import Framer

class Camera(Framer):
    thread = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    
    def __init__(self):
        """Start the background camera thread if it isn't running yet."""
        if Camera.thread is None:
            # start background frame thread
            Camera.thread = threading.Thread(target=self._thread)
            Camera.thread.start()

            # wait until frames are available
            while self.get_frame() is None:
                time.sleep(0)

    def get_frame(self):
        """Return the current camera frame."""
        return Camera.frame

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')
        
        while True:
            # read current frame
            _, img = camera.read()

            # encode as a jpeg image and return it
            yield img
#             yield cv2.imencode('.jpg', img)[1].tobytes()


    @classmethod
    def _thread(cls):
        """Camera background thread."""
        print('Starting camera thread.')
        frames_iterator = cls.frames()
        for frame in frames_iterator:
            Camera.frame = frame
