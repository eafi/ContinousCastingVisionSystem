import os

from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout
from CoreSystemGUI.ControlPanle.LogWidget import LogWidget


class ButtonListWidget(QWidget):
    def __init__(self, cfg):
        super(ButtonListWidget, self).__init__()
        self.cfg = cfg
        self.initUI()


    def initUI(self):
        # -创建button
        # -- 第一行 : 相机设置按钮 、 日志设置按钮
        self.button_visCamera1 = QPushButton(self.tr('Vis\nCamera 1'))  # 该按钮在main.py被绑定
        self.button_visCamera1.setFixedSize(80, 80)
        self.button_visCamera2 = QPushButton(self.tr('Vis\nCamera 2')) # 该按钮在main.py被绑定
        self.button_visCamera2.setFixedSize(80, 80)
        self.button_log = QPushButton(self.tr('LOG'))                  # 该按钮在main.py被绑定
        self.button_log.setFixedSize(80, 80)
        self.button_showLogDir = QPushButton(self.tr('Show Log\nDir'))  # 该按钮在main.py被绑定
        self.button_showLogDir.setFixedSize(80, 80)

        # -- 第二行 : 参考目标设置按钮
        self.button_setRefTar1 = QPushButton(self.tr('Set Ref\nTarget1'))  # 该按钮在main.py被绑定
        self.button_setRefTar1.setFixedSize(80, 80)
        self.button_setRefTar2 = QPushButton(self.tr('Set Ref\nTarget2'))  # 该按钮在main.py被绑定
        self.button_setRefTar2.setFixedSize(80, 80)
        self.button_setRefTar3 = QPushButton(self.tr('Set Ref\nTarget3'))  # 该按钮在main.py被绑定
        self.button_setRefTar3.setFixedSize(80, 80)
        self.button_setRefTar4 = QPushButton(self.tr('Set Ref\nTarget4'))  # 该按钮在main.py被绑定
        self.button_setRefTar4.setFixedSize(80, 80)
        self.button_setRefCons = QPushButton(self.tr('Set Ref\nConstrained'))  # 该按钮在main.py被绑定
        self.button_setRefCons.setFixedSize(80, 80)

        # -- 特殊More按钮
        self.button_moreSettings = QPushButton(self.tr('More')) # 该按钮在main.py 绑定
        # button list布局
        gridlayout = QGridLayout()
        gridlayout.addWidget(self.button_log, 0, 0)
        gridlayout.addWidget(self.button_showLogDir, 0, 1)
        gridlayout.addWidget(self.button_visCamera1, 0, 2)
        gridlayout.addWidget(self.button_visCamera2, 0, 3)
        gridlayout.addWidget(self.button_setRefTar1, 1, 0)
        gridlayout.addWidget(self.button_setRefTar2, 1, 1)
        gridlayout.addWidget(self.button_setRefTar3, 1, 2)
        gridlayout.addWidget(self.button_setRefTar4, 1, 3)
        gridlayout.addWidget(self.button_setRefCons, 1, 4)
        gridlayout.addWidget(self.button_moreSettings, 0, 4)
        self.setLayout(gridlayout)


    def logWidgetPop(self):
        """
        弹出日志配置控件
        :return:
        """
        self.logWidget = LogWidget(self.cfg)
        self.logWidget.exec()


    def logDirPop(self):
        """
        弹出当前日志目录文件夹
        :return:
        """
        import platform

        platName = platform.system()
        if 'Windows' in platName:
            os.system(f"explorer {self.cfg['Log_Conf']['LogDir']}")
        elif 'Linux' in platName:
            os.system(f"xdg-open {self.cfg['Log_Conf']['LogDir']}")





