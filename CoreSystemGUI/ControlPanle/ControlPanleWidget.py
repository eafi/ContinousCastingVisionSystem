from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from CoreSystemGUI.ControlPanle.StatusWidget import StatusWidget
from CoreSystemGUI.ControlPanle.ButtonListWidget import ButtonListWidget
from CoreSystemGUI.ControlPanle.VisualizationFrame import VisualizationFrame

class ControlPanleWidget(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.initUI()


    def initUI(self):
        # 左侧 : 状态 + 按钮 Widget
        vboxlayout = QVBoxLayout()
        self.statusWidget = StatusWidget(cfg=self.cfg)
        self.buttonWidget = ButtonListWidget(cfg=self.cfg)
        vboxlayout.addWidget(self.statusWidget)
        vboxlayout.addWidget(self.buttonWidget)

        # 右侧 : 可视化 Widget
        self.visualizationWidget = VisualizationFrame(cfg=self.cfg)
        hboxlayout = QHBoxLayout()
        hboxlayout.addLayout(vboxlayout)
        hboxlayout.addWidget(self.visualizationWidget)
        self.setLayout(hboxlayout)

