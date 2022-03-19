"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

调用Camera，在视窗中显示可以拖动的200x200区域，让用户将200x200像素区域覆盖到标定板上。

上述步骤完成了如下工作：
1. ROI坐标的确定，并记录在CONF文件中
2. 200x200像素覆盖保证了最小像素精度，确定了标定板与相机的距离关系
3. 多个ROIs覆盖在视窗中，对VOF进行了确定
"""

from PyQt5.QtWidgets import QWidget
from CoreSystemGUI.CameraPanle.CameraWidget import CameraWidget

class DistanceVOFCheck(QWidget):
    def __init__(self):
        super(DistanceVOFCheck, self).__init__()
        self.initUI()


    def initUI(self):
        self.cameraWidget = CameraWidget()

