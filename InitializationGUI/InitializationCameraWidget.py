from Modules.BaseCameraWidget import BaseCameraWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QRect, QPoint, QPointF
from PyQt5.QtCore import Qt
from Global_Val import Signal_Map
from Modules.parse import write_couple_cfg

class InitializationCameraWidget(BaseCameraWidget):
    def __init__(self, cameraType, cfg, ia):
        super(InitializationCameraWidget, self).__init__(cameraType=cameraType, ia=ia)
        self.cfg = cfg
        # Distance VOF检查: 绘制最小200x200的多个Rects
        self.isDrawMininumRects = False


    def paintEvent(self, event):
        super(InitializationCameraWidget, self).paintEvent(event=event)
        # ===========================================================================
        # 按钮事件： 绘制最小矩形
        # 首先绘制不动的最小矩形，数据来自于CFG文件，不动的最小矩形用于给用户参考
        if self.isDrawMininumRects:
            painter = QPainter()
            painter.begin(self)
            oldPen = painter.pen()
            pen = QPen()
            pen.setColor(Qt.red)
            pen.setWidth(4)
            painter.setPen(pen)
            windowW, windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
            ratioW = windowW / self.w  # 窗口 / 像素 <= 1.0
            ratioH = windowH / self.h
            for key in self.cfg['ROIs_Conf']:
                if self.cameraType in key:
                    rect = self.cfg['ROIs_Conf'][key]
                    rect = rect[0] * ratioW, rect[1] * ratioH, 200 * ratioW, 200 * ratioH
                    painter.drawRect(*rect)
                    painter.drawText(QPointF(rect[0] * ratioW, rect[1] * ratioH + 10), self.tr('Stay:'+key))
            painter.setPen(oldPen)
            painter.end()


    def show_moveable_rects(self):
        """
        依据cfg中的既有Rect ROI 产生可移动rect
        :return:
        """
        self.movableRects = []
        windowW, windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
        ratioW = windowW / self.w  # 窗口 / 像素 <= 1.0
        ratioH = windowH / self.h
        for key in self.cfg['ROIs_Conf']:
            if self.cameraType in key:
                rect = self.cfg['ROIs_Conf'][key]
                rect = rect[0] * ratioW, rect[1] * ratioH, 200 * ratioW, 200 * ratioH
                movableRect = MovaleRect(parent=self, whichCamerawhichROI=key,
                                          pos=QPoint(rect[0] * ratioW, rect[1] * ratioW))
                self.movableRects.append(movableRect)

    def slot_draw_mininum_rects(self):
        """
        响应 Distance & VOF Btn
        1. 根据CFG文件绘制ROI区域，并且以200x200的最小矩形绘制
        2. 交互： 用户应该拖动Rect到正确的标定板范围;
        3. 用户应该保证标定板面积大于等于200x200区域
        4. 当用户再次点击该按钮时，且rect确实发生移动时， 弹出让用户确认是否刷新CFG配置文件？且Rects消失
        :return:
        """
        # 第一次点击: 启动paintEvent绘制， 并启动可拖动movableRect与用户交互
        if self.isDrawMininumRects is False:
            self.isDrawMininumRects = True
            self.show_moveable_rects()
        # 第二次点击:
        else:
            # 检查矩形是否发生了移动:
            if self.is_any_rects_changed():
                ret = QMessageBox.question(self, self.tr('Caution!'), \
                                           self.tr('Are you sure to change the ROI RECT configuration?'), \
                                           QMessageBox.Yes, QMessageBox.No)
                if ret == QMessageBox.Yes:
                    self.write_new_rects()
            # 关闭paintEvent绘制
            self.isDrawMininumRects = False
            # 关闭movable Rects绘制:
            for movableRect in self.movableRects:
                movableRect.hide()


    def write_new_rects(self):
        """
        当用户第二次点击 Distance & VOF Btn 且 用户点击保存新rect位置时时，会把此时movable rects的数据覆盖到CFG文件中

        NOTE: slot操作会导致CFG文件发生变化，因此需要向系统发送CFG变化的信号
        :return:
        """
        for movableRect in self.movableRects:
            rect = self.cfg['ROIs_Conf'][movableRect.name]
            # 读取当前新的位置并覆盖掉原来的位置
            rect[0] = movableRect.parentCor.x()
            rect[1] = movableRect.parentCor.y()
            rect2str = str(rect[0])+','+str(rect[1])+','+str(rect[2])+','+str(rect[3])
            write_couple_cfg((movableRect.name, rect2str), path='../CONF.cfg')
        Signal_Map['CfgUpdateSignal'].emit()


    def is_any_rects_changed(self):
        """
        当用户第二次点击 Distance & VOF Btn 时, **检查当前cfg中保存的rect与新rect位置是否发生变化。**
        :return:
        """
        for movableRect in self.movableRects:
            rect = self.cfg['ROIs_Conf'][movableRect.name]  # cfg中保存的是初始化rect位置
            # 读取当前新的位置并覆盖掉原来的位置
            if rect[0] != movableRect.parentCor.x() or rect[1] != movableRect.parentCor.y():
                return True
        return False


class MovaleRect(QWidget):
    """
    可移动的rect矩形，让用户交互式的确定ROI的位置
    """
    def __init__(self, parent, whichCamerawhichROI, pos):
        """

        :param parent: 父类窗口： CameraWidget上绘制
        :param whichCamerawhichROI:
        :param pos:  初始化坐标
        """
        super(MovaleRect, self).__init__(parent=parent)
        self.setGeometry(0,0,200,200)
        self.name = whichCamerawhichROI
        self.parentCor = pos
        self.move(pos)
        self.show()

    def mousePressEvent(self, QMouseEvent):
        self.initX = QMouseEvent.x()
        self.initY = QMouseEvent.y()

    def mouseMoveEvent(self, QMouseEvent):
        x = QMouseEvent.x() - self.initX
        y = QMouseEvent.y() - self.initY

        self.parentCor = self.mapToParent(QPoint(x,y))
        self.move(self.parentCor)
        print(self.parentCor)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        oldPen = painter.pen()
        pen = QPen()
        pen.setColor(Qt.yellow)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawRect(QRect(0,0,200,200))
        painter.drawText(QPointF(0,10), self.tr('Movable:'+self.name))
        painter.setPen(oldPen)
        painter.end()