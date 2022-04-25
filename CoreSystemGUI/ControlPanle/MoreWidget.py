import numpy as np
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QApplication
from PyQt5.QtCore import QTimer, QRectF, pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QImage, QPainter, QPen, QPolygonF
import cv2

class MoreWidget(QWidget):
    """
    More 功能按键的总GUI， 包含了共八个ROI窗口+ 八个按钮
    这些窗口按照预定义的名字字典形式保存
    每一个窗口都是一个SingleMoreWidget组成
    """
    def __init__(self, cfg, left_camera, right_camera):
        super(MoreWidget, self).__init__()
        self.roi_names_dict = [
        'LeftCameraLeftROI',
        'LeftCameraRightROI',
        'LeftCameraBottomROI',
        'LeftCameraTopROI',
        'RightCameraLeftROI',
        'RightCameraRightROI',
        'RightCameraBottomROI',
        'RightCameraTopROI']
        self.single_widgets_dict = {}
        self.cfg = cfg
        self.left_camera = left_camera
        self.right_camera = right_camera
        self.paintTimer = QTimer()
        self.paintTimer.start(1000)
        self.paintTimer.timeout.connect(self.set_pics)
        self.init()

    def set_pics(self):
        for roi_name in self.roi_names_dict:
            if 'LeftCamera' in roi_name:
                img = self.left_camera.im_np  # 左相机图像
            else:
                img = self.right_camera.im_np
            roi = self.cfg['ROIs_Conf'][roi_name]  # 提取当前系统阶段所需要的ROI区域
            roi_img = img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
            self.single_widgets_dict[roi_name].view.set_pic(roi_img)
            self.single_widgets_dict[roi_name].update()


    def init(self):
        layout = QGridLayout()
        for i in range(8):
            single_widget = SingleMoreWidget(0.0, 0.0, 3.0, 20)
            layout.addWidget(single_widget, i//4, i%4)
            self.single_widgets_dict[self.roi_names_dict[i]] = single_widget

        self.setLayout(layout)



class SingleMoreWidget(QWidget):
    """
    More 功能按钮中， 单独的一个视窗， 包含一个用于显示相机ROI画面的ViewWidget; 以及一个按钮条，用于控制平衡值.
    """
    def __init__(self, default, left, right, steps):
        super(SingleMoreWidget, self).__init__()
        self.default = default
        self.left = left
        self.right = right
        self.steps = steps
        self.initUI()


    def initUI(self):
        self.windowW, self.windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
        self.valueBtn = ValueBtn(self.default, self.left, self.right, self.steps, parent=self)
        self.view = ViewWidget(parent=self)
        self.valueBtn.valueChanged.connect(self.view.slot_preprocess_view)
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.valueBtn)
        self.setLayout(layout)




class ViewWidget(QWidget):
    def __init__(self, parent):
        super(ViewWidget, self).__init__(parent=parent)
        self.pic = None
        self.val = 0.0
        self.setFixedSize(200, 200)

    def set_pic(self, pic):
        self.pic = pic


    def slot_preprocess_view(self, val):
        self.val = val


    def paintEvent(self, event):
        if self.pic is not None:
            painter = QPainter ()
            painter.begin(self)
            h, w = self.pic.shape
            pic = self.pic.astype(np.float32) / 255.0
            self.pic = pic + self.val * (pic - np.mean(pic))
            self.pic = np.clip(self.pic, 0., 1.0)
            self.pic = (self.pic * 255.0).astype(np.uint8)
            tmp_img = cv2.cvtColor(self.pic, cv2.COLOR_GRAY2RGB)  # 如果直接使用灰度，Qtpainter无法绘制
            qimage = QImage(tmp_img.data, w, h, 3 * w, QImage.Format_RGB888)
            self.windowW, self.windowH = self.width(), self.height()  # 对窗口进行缩放，实时修正尺寸
            self.ratioW = self.windowW / w  # 窗口 / 像素 <= 1.0
            self.ratioH = self.windowH / h
            painter.drawImage(QRectF(0, 0, self.windowW, self.windowH),
                              qimage, QRectF(0, 0, w, h))
            painter.end()


class ValueBtn(QWidget):
    valueChanged = pyqtSignal(float)
    def __init__(self,defaultVal, startVal, endVal, steps, parent):
        """

        :param defaultVal: 初始值
        :param startVal:  左下线
        :param endVal:  右上线
        :param steps:  增增量数
        """
        super(ValueBtn, self).__init__(parent=parent)
        self.upBtn = QPushButton(self.tr('UP'))
        self.upBtn.clicked.connect(self.up_slot)
        self.downBtn = QPushButton(self.tr('Down'))
        self.downBtn.clicked.connect(self.down_slot)
        self.text = QLabel(self.tr('{:.2f}'.format(defaultVal)))
        layout = QHBoxLayout()
        layout.addWidget(self.text)
        layout.addWidget(self.upBtn)
        layout.addWidget(self.downBtn)
        self.setLayout(layout)

        self.currVal = defaultVal
        self.valueChanged.emit(self.currVal)
        self.accVal = (endVal-startVal) / steps
        self.endVal = endVal
        self.startVal = startVal


    def up_slot(self):
        self.currVal = min(self.currVal + self.accVal, self.endVal)
        self.text.setText(self.tr('{:.2f}'.format(self.currVal)))
        self.valueChanged.emit(self.currVal)

    def down_slot(self):
        self.currVal = max(self.currVal - self.accVal, self.startVal)
        self.text.setText(self.tr('{:.2f}'.format(self.currVal)))
        self.valueChanged.emit(self.currVal)



import sys
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MoreWidget()
    ex.show()
    sys.exit(app.exec())