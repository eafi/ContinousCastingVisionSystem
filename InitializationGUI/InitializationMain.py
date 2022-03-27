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
from InitializationCameraWidget import InitializationCameraWidget
from InitializationGUI.calibration import CalibrationWidget
from harvesters.core import Harvester
from platform import system


class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.sysName = system()
        self.cfgManager = CfgManager(path='../CONF.cfg', platform=self.sysName)
        self.initUI()
        self.clickedBinding()

    def initUI(self):
        self.setWindowTitle(self.tr('Initialization'))
        self.btn1 = QPushButton(self.tr('Distance & VOF\nCheck'))  # 距离与视场检查
        self.btn1.setFixedSize(120, 80)
        self.btn2 = QPushButton(self.tr('Hand-Eye\nCalibration'))  # 手眼标定
        self.btn2.setFixedSize(120, 80)
        #self.btn3 = QPushButton(self.tr('Camera\nCalibration'))  # 相机标定
        #self.btn3.setFixedSize(120, 80)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.btn1)
        btnLayout.addWidget(self.btn2)

        #============== Camera =========================
        self.h = Harvester()
        if self.sysName == 'Linux':
            self.h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
        else:
            self.h.add_file('C:/Program Files/MATRIX VISION/mvIMPACT Acquire/bin/x64/mvGenTLProducer.cti')
        self.h.update()
        print(self.h.device_info_list)
        self.camera_1 = self.h.create_image_acquirer(0)
        self.camera_2 = self.h.create_image_acquirer(1)
        self.camera_1.start()
        self.camera_2.start()
        self.leftCamera = InitializationCameraWidget(cfg=self.cfgManager.cfg, cameraType=self.tr('LeftCamera'), harvesters=self.camera_1)
        self.rightCamera = InitializationCameraWidget(cfg=self.cfgManager.cfg, cameraType=self.tr('RightCamera'), harvesters=self.camera_2)
        self.leftCamera.setFixedSize(self.leftCamera.w, self.leftCamera.h)
        self.rightCamera.setFixedSize(self.rightCamera.w, self.rightCamera.h)


        #============== Calibration =================
        self.calibration = CalibrationWidget(cfg=self.cfgManager.cfg, parent=self)

        cameraLayout = QHBoxLayout()
        cameraLayout.addWidget(self.leftCamera)
        cameraLayout.addWidget(self.rightCamera)

        layout = QVBoxLayout()
        layout.addLayout(btnLayout)
        layout.addLayout(cameraLayout)

        self.setLayout(layout)
        self.show()

    def clickedBinding(self):
        #self.distanceVOF = DistanceVOFCheck(self.cfgManager.cfg)
        self.btn1.clicked.connect(self.leftCamera.slot_draw_mininum_rects)
        self.btn1.clicked.connect(self.rightCamera.slot_draw_mininum_rects)

        self.btn2.clicked.connect(self.calibration.slot_init)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec())
