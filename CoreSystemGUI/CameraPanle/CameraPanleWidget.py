from PyQt5.QtWidgets import QWidget
from CoreSystemGUI.CameraPanle.CameraWidget import CameraWidget
from PyQt5.QtWidgets import QHBoxLayout

class CameraPanleWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.resize(1000,1000)
        self.initUI()

    def initUI(self):
        self.leftCameraWidget = CameraWidget()
        self.rightCameraWidget = CameraWidget()
        hbox = QHBoxLayout()
        hbox.addWidget(self.leftCameraWidget)
        hbox.addWidget(self.rightCameraWidget)
        self.setLayout(hbox)

