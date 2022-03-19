from PyQt5.QtWidgets import QDialog, QFrame, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox, \
    QPushButton, QWidget
from Modules.parse import write_couple_cfg
from Global_Val import Signal_Map


class LogWidget(QDialog):
    def __init__(self, cfg):
        super(LogWidget, self).__init__()
        self.currentCfg = cfg
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.tr('Log Configure'))

        vboxlayout = QVBoxLayout()
        self.logTypeFrame = LogTypeFrame(cfg=self.currentCfg)
        self.logDirLabel = LogDirLabel(cfg=self.currentCfg)
        self.saveQuitBtn = LogSaveWidget(cfg=self.currentCfg)
        vboxlayout.addWidget(self.logTypeFrame)
        vboxlayout.addWidget(self.logDirLabel)
        vboxlayout.addWidget(self.saveQuitBtn)
        self.setLayout(vboxlayout)

        # 日志的按键绑定
        self.saveQuitBtn.logSaveBtn.clicked.connect(self.saveSlot)
        self.saveQuitBtn.logQuitBtn.clicked.connect(self.close)


    def saveSlot(self):
        ret = QMessageBox.question(self, self.tr('Caution!'), \
                                   self.tr('Are you sure to change the log configuration?'), \
                                   QMessageBox.Yes, QMessageBox.No)
        if ret == QMessageBox.Yes:
            write_couple_cfg(self.logTypeFrame.updateCfg())
            write_couple_cfg(self.logDirLabel.updateCfg())
            Signal_Map['CfgUpdateSignal'].emit()


class LogTypeFrame(QFrame):
    """
    LOG配置 ： 日志类型勾选框
    默认情况下，文字类型的日志是无法取消的.
    """
    def __init__(self, cfg):
        super(LogTypeFrame, self).__init__()
        self.cfg = cfg
        self.parseTypeCfg(self.cfg)
        self.initUI()


    def initUI(self):
        self.setFrameShape(QFrame.Panel)  # 框线

        vboxlayout = QVBoxLayout()
        self.decriptionLabel = QLabel(self.tr('Log Type'))
        vboxlayout.addWidget(self.decriptionLabel)
        hboxlayout = QHBoxLayout()

        # 文本类型日志框选
        self.textCheckBox = QCheckBox(self.tr('Text'))
        self.textCheckBox.toggle()
        self.textCheckBox.setDisabled(True)

        # 图片类型日志框选
        self.imageCheckBox = QCheckBox(self.tr('Image'))
        if self.currentImageCheckBox is True:
            self.imageCheckBox.click()


        # 样式
        hboxlayout.addWidget(self.textCheckBox)
        hboxlayout.addWidget(self.imageCheckBox)
        vboxlayout.addLayout(hboxlayout)
        self.setLayout(vboxlayout)



    def parseTypeCfg(self, cfg):
        currentTypeCfg = cfg['Log_Conf']['LogType'].split(',')
        self.currentTextCheckBox = True if 'text' in currentTypeCfg else True  # 注意！ 默认情况下始终保证文本日志功能
        self.currentImageCheckBox = True if 'image' in currentTypeCfg else False


    def updateCfg(self):
        """
        在Log点击保存时，检查配置是否更新
        :return:
        """
        if self.imageCheckBox.isChecked() == True and self.currentImageCheckBox == False:
            self.cfg['Log_Conf']['LogType'] = 'text,image'
            return 'LogType', 'text,image'
        elif self.imageCheckBox.isChecked() == False and self.currentImageCheckBox == True:
            self.cfg['Log_Conf']['LogType'] = 'text'
            return 'LogType', 'text'
        return '',''



class LogDirLabel(QLabel):
    """
    LOG配置 ： 日志保存的目录
    使用Label显示当前保存的目录，点击后可以修改到新的目录
    """
    def __init__(self, cfg):
        super(LogDirLabel, self).__init__()
        self.cfg = cfg
        self.oldDir = cfg['Log_Conf']['LogDir']
        self.newDir = ''
        self.initUI(frameShadow=QFrame.Raised, dir=self.oldDir)

    def initUI(self, frameShadow, dir):
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(frameShadow)
        self.setText(self.tr('Log Dir: ')+self.tr(dir))


    def mousePressEvent(self, QMouseEvent):
        self.setFrameShadow(QFrame.Sunken)
        self.newDir = QFileDialog.getExistingDirectory(self, self.tr('Choose new Log Dir'), self.oldDir)
        self.initUI(frameShadow=QFrame.Raised, dir=self.newDir)


    def updateCfg(self):
        if self.newDir != '' and self.newDir != self.oldDir:
            self.cfg['Log_Conf']['LogDir'] = self.newDir
            return 'LogDir', self.newDir
        return '',''



class LogSaveWidget(QWidget):
    """
    LOG配置 ： 选择保存当前日志配置或不保存并退出
    """
    def __init__(self, cfg):
        super(LogSaveWidget, self).__init__()
        self.currentCfg = cfg
        self.initUI()


    def initUI(self):
        hboxlayout = QHBoxLayout()
        self.logSaveBtn = QPushButton(self.tr('save'))
        self.logQuitBtn = QPushButton(self.tr('quit'))
        hboxlayout.addWidget(self.logSaveBtn)
        hboxlayout.addWidget(self.logQuitBtn)
        self.setLayout(hboxlayout)



