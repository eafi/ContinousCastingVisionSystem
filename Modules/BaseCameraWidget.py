# TODO: 相机的采样频率与处理的采样频率相等.
import cv2
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QTimer, QRectF, pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QImage, QPainter, QPen, QPolygonF
from Modules import camera, fakeCamera
from Modules.LOG import *
import numpy as np
from collections import deque
class BaseCameraWidget(QWidget):
    cameraStatusSignal = pyqtSignal(str)

    def __init__(self, cfg, cameraType, harvesters):
        """

        :param cfg:
        :param cameraType:相机的类型， LeftCamera or RightCamera
        :param harvesters:
        :param mtx: 当为初始化时，并不需要反畸变
        :param dist:
        """
        super(BaseCameraWidget, self).__init__()
        self.im_np = None
        self.fps = 66
        self.cameraType = cameraType
        self.ia = harvesters

        # 是否绘制ROIs
        self.isDrawROIs = False

        lr_name = self.cameraType.split('Camera')[0]
        self.init()



    def status_update(self):
        """
        定时发送相机状态. 并且读取一帧图像
        :return:
        """
        if self.camera is not None:
            self.im_np = self.camera.capture()
            if self.im_np is not None:
                self.h, self.w = self.im_np.shape
                self.cameraStatusSignal.emit('OK')
                if not self.paintTimer.isActive():
                    self.paintTimer.start(self.fps)
                return True
        else:
            self.cameraStatusSignal.emit('Break')
            # 尝试重新与相机建立链接
            self.try_init_camera()
            if self.paintTimer is not None:
                self.paintTimer.stop()
        return False


    def init(self):
        """
        初始化相机相关资源:
        0. 读取CFG文件，将ROI rect信息读入
        1. 相机画面刷新定时器, 并开启绘图定时
        2. 相机状态反馈定时器，并开启状态定时反馈
        3. 尝试获得一帧图像，从而判断相机系统是否可用，并设定CameraWidget的宽度和高度到该尺寸
        4. 是否绘制ROIs控制变量 = False
        5. 是否绘制Targets变量 = False
        :return:
        """


        self.setWindowTitle(self.cameraType)
        self.try_init_camera()
        self.paintTimer = QTimer()
        self.paintTimer.start(self.fps)

        self.paintTimer.timeout.connect(self.update)  # 定时更新画面
        #self.statuTimer.timeout.connect(self.status)  # 定时汇报模组状态


    def try_init_camera(self):
        """
        初始化相机资源，如果初始化失败，将会返回None
        :return:
        """
        try:
            self.camera = camera.Camera(ia=self.ia)
            #self.camera = fakeCamera.Camera()
            # 此处获得图像只为获得图像的尺寸信息以及初始化
            self.im_np = self.camera.capture()
            if self.im_np is not None:
                self.h, self.w = self.im_np.shape
                self.cameraStatusSignal.emit('OK')
                self.resize(self.w, self.h)
            #self.camera = fakeCamera.Camera()  # 调试用
            LOG(log_types.OK, self.tr(self.cameraType+': Camera Init OK.'))
        except Exception as e:
            # 相机资源初始化失败
            LOG(log_types.WARN, self.tr(self.cameraType+': Camera Init failed. '+e.args[0]))
            self.cameraStatusSignal.emit('Break')
            self.camera = None



    def paintEvent(self, event):
        """
        实时更新相机视窗的Windows Width, Height， 以及与image的 ratio.
        :param event:
        :return:
        """
        self.status_update()
        if self.camera is not None and self.im_np is not None:
            painter = QPainter()
            painter.begin(self)
            tmp_img = cv2.cvtColor(self.im_np, cv2.COLOR_GRAY2RGB) # 如果直接使用灰度，Qtpainter无法绘制
            qimage = QImage(tmp_img.data, self.w, self.h, 3 * self.w, QImage.Format_RGB888)
            self.windowW, self.windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
            self.ratioW = self.windowW / self.w  # 窗口 / 像素 <= 1.0
            self.ratioH = self.windowH / self.h
            painter.drawImage(QRectF(0, 0, self.windowW, self.windowH),
                              qimage, QRectF(0, 0, self.w, self.h))

            if self.isDrawROIs:
                pen = QPen()
                pen.setColor(Qt.red)
                pen.setWidth(2)
                painter.setPen(pen)
                for key in self.cfg['ROIs_Conf']:
                    if self.cameraType in key:
                        rect = self.cfg['ROIs_Conf'][key]
                        rect = rect[0]*self.ratioW, rect[1]*self.ratioH, rect[2]*self.ratioW, rect[3]*self.ratioH
                        painter.drawRect(*rect)
                        name = key.split('Camera')[0][0] + key.split('Camera')[1][0]
                        painter.drawText(QPointF(rect[0]+2, rect[1]+20), self.tr(name))
            painter.end()







