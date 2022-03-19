"""
==================
Author: Yifei Zhang
Email: imeafi@gmail.com
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout
from PyQt5.QtCore import QObject
from Modules.system import *

class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.core = CoreSystem()
        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.tr('Initialization'))
        self.btn1 = QPushButton(self.tr('Distance & VOF\nCheck'))  # 距离与视场检查
        self.btn1.setFixedSize(80, 80)
        self.btn2 = QPushButton(self.tr('Robot-Eye\nCalibration'))  # 手眼标定
        self.btn2.setFixedSize(80, 80)
        self.btn3 = QPushButton(self.tr('Camera\nCalibration'))  # 相机标定
        self.btn3.setFixedSize(80, 80)

        layout = QHBoxLayout()
        layout.addWidget(self.btn1)
        layout.addWidget(self.btn2)
        layout.addWidget(self.btn3)
        self.setLayout(layout)
        self.show()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainGUI()
    sys.exit(app.exec())