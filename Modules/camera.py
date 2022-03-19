'''
A simple Program for grabing video from basler camera and converting it to opencv img.
Tested on Basler acA1300-200uc (USB3, linux 64bit , python 3.5)
'''
from pypylon import pylon
from pypylon import genicam
from PyQt5.QtCore import QObject
from Modules.LOG import *


class Camera(QObject):

    def __init__(self):
        super(Camera, self).__init__()
        # conecting to the first available camera
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.converter = pylon.ImageFormatConverter()
        # converting to opencv bgr format
        self.converter.OutputPixelFormat = pylon.PixelType_Mono8
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


    def capture(self):
        # Grabing Continusely (video) with minimal delay
        img = None
        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                # Access the image data
                image = self.converter.Convert(grabResult)
                img = image.GetArray()
            grabResult.Release()
            self.camera.StopGrabbing()
        except (genicam.RuntimeException ,genicam.LogicalErrorException):
            LOG(log_types.WARN, self.tr('Camera Capturing is Failed.'))
            return None

        return img






