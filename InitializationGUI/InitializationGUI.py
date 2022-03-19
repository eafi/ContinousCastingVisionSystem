"""
==================
Author: Yifei Zhang
Email: imeafi@gmail.com
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QObject
from distanceVofCheck import DistanceVOFCheck
from Modules.parse import CfgManager
from CoreSystemGUI.CameraPanle.CameraWidget import CameraWidget


class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.cfgManager = CfgManager()
        self.initUI()
        self.clickedBinding()

    def initUI(self):
        self.setWindowTitle(self.tr('Initialization'))
        self.btn1 = QPushButton(self.tr('Distance & VOF\nCheck'))  # 距离与视场检查
        self.btn1.setFixedSize(80, 80)
        self.btn2 = QPushButton(self.tr('Robot-Eye\nCalibration'))  # 手眼标定
        self.btn2.setFixedSize(80, 80)
        self.btn3 = QPushButton(self.tr('Camera\nCalibration'))  # 相机标定
        self.btn3.setFixedSize(80, 80)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.btn1)
        btnLayout.addWidget(self.btn2)
        btnLayout.addWidget(self.btn3)

        self.leftCamera = CameraWidget(self.cfgManager.cfg, self.tr('LeftCamera'))
        self.leftCamera.setFixedSize(800, 600)
        self.rightCamera = CameraWidget(self.cfgManager.cfg, self.tr('RightCamera'))
        self.rightCamera.setFixedSize(800, 600)
        cameraLayout = QHBoxLayout()
        cameraLayout.addWidget(self.leftCamera)
        cameraLayout.addWidget(self.rightCamera)

        layout = QVBoxLayout()
        layout.addLayout(btnLayout)
        layout.addLayout(cameraLayout)

        self.setLayout(layout)
        self.show()

    def clickedBinding(self):
        self.distanceVOF = DistanceVOFCheck(self.cfgManager.cfg)
        self.btn1.clicked.connect(self.distanceVOF.show)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec())
