from Modules.BaseCameraWidget import BaseCameraWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QRect, QPoint, QPointF
from PyQt5.QtCore import Qt
from Global_Val import Signal_Map
from Modules.parse import write_couple_cfg

class InitializationCameraWidget(BaseCameraWidget):
    def __init__(self, cameraType, cfg, harvesters):
        super(InitializationCameraWidget, self).__init__(cfg=cfg, cameraType=cameraType, harvesters=harvesters)
        self.cfg = cfg



    def paintEvent(self, event):
        super(InitializationCameraWidget, self).paintEvent(event=event)


    def show_moveable_rects(self):
        """
        依据cfg中的既有Rect ROI 产生可移动rect
        :return:
        """
        self.movableRects = []
        for key in self.cfg['ROIs_Conf']:
            if self.cameraType in key:
                rect = self.cfg['ROIs_Conf'][key]
                rect = rect[0] * self.ratioW, rect[1] * self.ratioH, 200 * self.ratioW, 200 * self.ratioH
                movableRect = MovaleRect(parent=self, whichCamerawhichROI=key,
                                          pos=QPoint(rect[0], rect[1]), rw=self.ratioW, rh=self.ratioH)
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
        if not self.isDrawROIs:
            self.isDrawROIs = True
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
            self.isDrawROIs = False
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
            rect[0] = int(movableRect.parentCor.x() / self.ratioW)
            rect[1] = int(movableRect.parentCor.y() / self.ratioH)
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
    def __init__(self, parent, whichCamerawhichROI, pos, rw, rh):
        """

        :param parent: 父类窗口： CameraWidget上绘制
        :param whichCamerawhichROI:
        :param pos:  初始化坐标
        """
        super(MovaleRect, self).__init__(parent=parent)
        self.setGeometry(0,0,200*rw,200*rh)
        self.rw = rw
        self.rh = rh
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
        painter.drawRect(QRect(0,0,200*self.rw,200*self.rh))
        name = self.name.split('Camera')[0][0] + self.name.split('Camera')[1][0]
        painter.drawText(QPointF(2,20), self.tr('Move:'+name))
        painter.setPen(oldPen)
        painter.end()