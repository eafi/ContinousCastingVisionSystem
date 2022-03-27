'''
A simple Program for grabing video from basler camera and converting it to opencv img.
Tested on Basler acA1300-200uc (USB3, linux 64bit , python 3.5)
'''
import cv2
from pypylon import pylon
from pypylon import genicam
from PyQt5.QtCore import QObject
from Modules.LOG import *


class Camera(QObject):

    def __init__(self, ia):
        super(Camera, self).__init__()
        self.camera_ia = ia
        #self.camera_ia.start()

    def capture(self):
        # Grabing Continusely (video) with minimal delay
        img = None
        try:
            buffer = self.camera_ia.fetch()
            payload = buffer.payload
            component = payload.components[0]
            width = component.width
            height = component.height

            # Reshape the image so that it can be drawn on the VisPy canvas:
            img = component.data.reshape(height, width)
            img = cv2.resize(img, (1280,1024))
            buffer.queue()
        except Exception as e:
            LOG(log_types.WARN, self.tr('Camera Capturing is Failed.'+e.args[0]))
            return None
        return img


from harvesters.core import Harvester
if __name__ == '__main__':
    h = Harvester()
    h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
    h.update()
    c = Camera(ia=h.create_image_acquirer(1))
    c2 = Camera(ia=h.create_image_acquirer(2))
    while True:
        img = c.capture()
        if img is not None:
        #img2 = c2.capture()
            cv2.imshow('df', img)
            cv2.waitKey(33)
