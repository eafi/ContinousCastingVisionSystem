# TODO: 相机的采样频率与处理的采样频率相等.
import cv2
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, QRectF, pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QImage, QPainter, QPen, QPolygonF
from Modules import camera, fakeCamera
from Modules.LOG import *
import numpy as np
from Modules.BaseCameraWidget import BaseCameraWidget
class CoreSystemCameraWidget(BaseCameraWidget):

    def __init__(self, cameraType, cfg, harvesters):
        super(CoreSystemCameraWidget, self).__init__(cfg=cfg, cameraType=cameraType, harvesters=harvesters)
        self.cfg = cfg
        self.rect = None  # 用于绘制Target
        # 是否绘制Targets
        self.isDrawTargets = True



    def paintEvent(self, event):
        super(CoreSystemCameraWidget, self).paintEvent(event=event)  # 绘制基本Camera图像
        # ========================================================================================== #
        # 绘制派生类的定制图像
        if self.camera is not None and self.im_np is not None:
            painter = QPainter()
            painter.begin(self)
            oldPen = painter.pen()

            # 绘制Target区域
            if self.isDrawTargets and self.rect is not None:
                pen = QPen()
                pen.setColor(Qt.green)
                painter.setPen(pen)
                # 将绘图缩放到适合当前窗口
                rect = self.rect * np.array([self.ratioW, self.ratioH])
                painter.drawPolyline(QPolygonF(map(lambda p: QPointF(*p),rect)))

            painter.setPen(oldPen)
            painter.end()


    def toggle_rois(self, state):
        """
        勾选： 是否绘制ROI
        :param state:
        :return:
        """
        if state == Qt.Checked:
            self.isDrawROIs = True
        else:
            self.isDrawROIs = False



    def found_targets_slot(self, whichCamerawhichROI: str, rect: np.ndarray):
        if self.cameraType in whichCamerawhichROI and rect.size != 0:
            self.rect = rect


    def toggle_targets(self, state):
        """
        勾选： 是否绘制Target
        :param state:
        :return:
        """
        if state == Qt.Checked:
            self.isDrawTargets = True
        else:
            self.isDrawTargets = False

    def get_roiImages(self):
        """
        获得受到ROI控制的局部图像，由于可能存在多个ROI区域，返回列别
        :return: map of region of interests, e.g. 'LeftCameraLeftRoi' : [.., .., .., ..]
        """
        roiImages = {}
        for key in self.cfg['ROIs_Conf']:
            if self.cameraType in key:
                roi = self.cfg['ROIs_Conf'][key]
                roiImages[key] = (self.im_np[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]])
        return roiImages

    def get_a_roiImage(self, whichCamerawhichROI: str):
        """
        选取特定的ROI区域
        :return:
        """
        roi = self.cfg['ROIs_Conf'][whichCamerawhichROI]
        return self.im_np[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]







