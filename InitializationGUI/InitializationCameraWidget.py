from Modules.BaseCameraWidget import BaseCameraWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRectF, QPoint

class InitializationCameraWidget(BaseCameraWidget):
    def __init__(self, cameraType, cfg):
        super(InitializationCameraWidget, self).__init__(cameraType=cameraType)
        self.cfg = cfg
        # Distance VOF检查: 绘制最小200x200的多个Rects
        self.isDrawMininumRects = False
        self.moveableRect = MovealeRect()
        self.move(50,50)
        self.resize(800,600)



class MovealeRect(QWidget):
    """
    可移动的rect矩形，让用户交互式的确定ROI的位置
    """
    def __init__(self):
        super(MovealeRect, self).__init__()


    def mousePressEvent(self, QMouseEvent):
        self.initX = QMouseEvent.x()
        self.initY = QMouseEvent.y()


    def mouseMoveEvent(self, QMouseEvent):
        x = QMouseEvent.x() - self.initX
        y = QMouseEvent.y() - self.initY

        self.move(self.mapToParent(QPoint(x,y)))


    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.drawRect(QRectF(0,0,200,200))
        painter.end()