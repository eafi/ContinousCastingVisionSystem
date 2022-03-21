"""
=========
Author: Yifei Zhang
Email: imeafi@gmail.com

StatusWidget is used for showing the system status.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from Modules.LOG import *


ClrMap = {
    'g' : (0, 255, 0),  # 连接通讯正常
    'r' : (255, 0, 0),  # 连接断掉
    'y' : (0, 255, 255)  # 连接但没有正确的数据通讯
}


class StatusWidget(QWidget):
    def __init__(self, cfg):
        super(StatusWidget, self).__init__()
        self.cfg = cfg
        self.leftCameraStatusLabel = aStatusLabel(cfg=cfg, description='LeftCamera', status='Break') # 在coresystemmain.py 中绑定
        self.rightCameraStatusLabel = aStatusLabel(cfg=cfg, description='RightCamera', status='Break')
        self.cudaStatusLabel = aStatusLabel(cfg=cfg, description='CUDA', status='Break')
        self.robotStatusLabel = aStatusLabel(cfg=cfg, description='RobotCom', status='Break')
        self.initUI()


    def initUI(self):
        layout = QGridLayout()
        layout.addWidget(self.leftCameraStatusLabel, 0, 0)
        layout.addWidget(self.rightCameraStatusLabel, 0, 1)
        layout.addWidget(self.cudaStatusLabel, 1, 0)
        layout.addWidget(self.robotStatusLabel, 1, 1)

        self.setLayout(layout)





class aStatusLabel(QWidget):
    def __init__(self, cfg, description, status):
        super(aStatusLabel, self).__init__()
        self.description = description
        self.cfg = cfg
        self.initUI(status, description)

    def initUI(self, status, description):
        self.icon = QLabel(self)

        self.text = QLabel(self)
        self.text.setText(self.tr(description))

        hboxlayout = QHBoxLayout()
        hboxlayout.addWidget(self.icon)
        hboxlayout.addWidget(self.text)
        hboxlayout.setSpacing(5)
        self.setLayout(hboxlayout)
        self.clrChange(status)


    def clrChange(self, newStatus):
        newClr = ClrMap[self.cfg['WarnColor_Conf'][newStatus]]
        img_np = np.zeros((20,20,3), dtype=np.uint8)
        img_np[1:-1, 1:-1, :] = newClr
        h, w, c = img_np.shape
        qimage = QImage(img_np.data, w, h, 3*w, QImage.Format_RGB888)
        self.icon.setPixmap(QPixmap.fromImage(qimage))
        self.update()






