'''
A simple Program for grabing video from basler camera and converting it to opencv img.
Tested on Basler acA1300-200uc (USB3, linux 64bit , python 3.5)
'''
import cv2
import numpy as np
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
            img = img.astype(np.uint8)
            #img = 255 - img.astype(np.uint8)
            #img = img.astype(np.uint8)
            buffer.queue()
        except Exception as e:
            LOG(log_types.WARN, self.tr('Camera Capturing is Failed.'+e.args[0]))
            return None
        return img


from harvesters.core import Harvester
from platform import system
if __name__ == '__main__':
    h = Harvester()
    if system() == 'Linux':
        h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
    else:
        h.add_file('C:/Program Files/MATRIX VISION/mvIMPACT Acquire/bin/x64/mvGenTLProducer.cti')
    h.update()
    # 90: 左  91： 右
    ia = h.create_image_acquirer(serial_number='S1101390')
    #ia2 = h.create_image_acquirer(1)
    ia.start()
    #ia2.start()
    c = Camera(ia=ia)
    #c2 = Camera(ia=ia2)
    #from Modules.Robot import Robot
    #from Modules.parse import CfgManager
    #cfgManager = CfgManager(path='../CONF.cfg')
    #cfg = cfgManager.cfg
    #robot = Robot(cfg=cfg)
    #robot.start()  # 不停发送系统状态
    #robot.set_light_on()

    count = 0
    from time import sleep
    h = 11
    w = 8
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    while True:
        img = c.capture()
        #img2 = c2.capture()
        if img is not None:
        #img2 = c2.capture()
            cv2.imshow('df', cv2.resize(img, None, fx=0.5, fy=0.5))
            #cv2.imshow('df2', cv2.resize(img2, None, fx=0.5, fy=0.5))
            k = cv2.waitKey(33)
            if k == 99: # 'c'
                cv2.imwrite(f'C:/Users/001/Desktop/imgs/{count}.bmp', img)
                count += 1

