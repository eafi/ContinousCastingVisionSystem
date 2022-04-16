import numpy as np
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QTimer, QRectF, pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QImage, QPainter, QPen, QPolygonF
import cv2

class MoreWidget(QWidget):
    def __init__(self):
        super(MoreWidget, self).__init__()



class SingleMoreWidget(QWidget):
    def __init__(self):
        super(SingleMoreWidget, self).__init__()
        self.pic = None
        self.paintTimer = QTimer()
        self.paintTimer.start(1000)
        self.paintTimer.timeout.connect(self.update)
        self.initUI()


    def initUI(self):
        self.valueBtn = ValueBtn(0.4, 0.1, 1.0, 10)
        layout = QVBoxLayout()
        layout.addWidget(self.valueBtn)
        self.setLayout(layout)




    def getPic(self, pic):
        self.pic = pic

    def paintEvent(self, event):
        if self.pic is not None:
            painter = QPainter ()
            painter.begin(self)
            tmp_img = cv2.cvtColor(self.pic, cv2.COLOR_GRAY2RGB)  # 如果直接使用灰度，Qtpainter无法绘制
            qimage = QImage(tmp_img.data, self.w, self.h, 3 * self.w, QImage.Format_RGB888)
            self.windowW, self.windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
            self.ratioW = self.windowW / self.w  # 窗口 / 像素 <= 1.0
            self.ratioH = self.windowH / self.h
            painter.drawImage(QRectF(0, 0, self.windowW, self.windowH),
                              qimage, QRectF(0, 0, self.w, self.h))


class ValueBtn(QWidget):
    def __init__(self,defaultVal, startVal, endVal, steps):
        super(ValueBtn, self).__init__()
        self.upBtn = QPushButton(self.tr('UP'))
        self.upBtn.clicked.connect(self.upSlot)
        self.downBtn = QPushButton(self.tr('Down'))
        self.downBtn.clicked.connect(self.downSlot)
        self.text = QLabel(self.tr(str(defaultVal)))
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.upBtn)
        layout.addWidget(self.downBtn)
        self.setLayout(layout)

        self.currVal = defaultVal
        self.accVal = (endVal-startVal) / steps
        self.endVal = endVal
        self.startVal = startVal


    def upSlot(self):
        self.currVal = min(self.currVal + self.accVal, self.endVal)
        self.text.setText(self.tr(str(self.currVal)))

    def downSlot(self):
        self.currVal = max(self.currVal - self.accVal, self.startVal)
        self.text.setText(self.tr(str(self.currVal)))



if __name__ == "__main__":
    pass