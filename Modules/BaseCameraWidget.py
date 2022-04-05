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
        super(BaseCameraWidget, self).__init__()
        self.im_np = None
        self.fps = 66
        self.cameraType = cameraType # 相机的类型， LeftCamera or RightCamera
        self.ia = harvesters

        calibrationmtx = cfg['HandEyeCalibration_Conf']
        self.mtx = calibrationmtx[f'{cameraType}Matrix']
        self.dist = calibrationmtx[f'{cameraType}Dist']
        self.init()


    def status(self):
        """
        定时发送相机状态. 并且读取一帧图像
        :return:
        """
        if self.camera is not None:
            self.im_np = self.camera.capture()
            # 矫正
            self.im_np = cv2.remap(self.im_np, self.mapx, self.mapy, cv2.INTER_LINEAR)
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
        #self.statuTimer = QTimer()
        self.paintTimer = QTimer()
        #self.statuTimer.start(self.fps)
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
                # 明确相机的畸变和内参数矩阵
                self.newCameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (self.w, self.h), 1, (self.w, self.h))
                # 重映射矩阵
                self.mapx, self.mapy = cv2.initUndistortRectifyMap(self.mtx, self.dist, None, self.newCameramtx, (self.w, self.h), 5)
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
        self.status()
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
            painter.end()







