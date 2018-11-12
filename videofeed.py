import cv2
import numpy as np
import io
from PIL import Image

class VideoFeed:
    def __init__(self,name="w1",capture=1):
        self.camera_index = 0
        self.name = name
        if capture == 1:
            self.cam = cv2.VideoCapture(self.camera_index)
            if not self.cam.isOpened():
                self.cam.open(self.camera_index)

    def get_frame(self):
        ret_val, img = self.cam.read()
        c = cv2.waitKey(1)

        cv2.imshow('MY WEBCAM', img)
        cv2_im = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_im = Image.fromarray(cv2_im)
        b = io.BytesIO()
        pil_im.save(b, 'jpeg')
        im_bytes = b.getvalue()
        return im_bytes

    def set_frame(self, frame_bytes):
        pil_bytes = io.BytesIO(frame_bytes)
        pil_image = Image.open(pil_bytes)
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        print(cv_image.shape)
        cv2.imshow(self.name, cv_image)

if __name__=="__main__":
    vf = VideoFeed("MAIN", 1)
    while 1:
        m = vf.get_frame()
        vf.set_frame(m)

