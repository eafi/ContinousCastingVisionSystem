from PyQt5.QtWidgets import QWidget, QMessageBox, QPushButton, QHBoxLayout, QTextEdit, QVBoxLayout
from Modules.Robot import Robot
from Modules.LOG import *
import cv2
from PyQt5.QtCore import QThread
from Modules.calibration import calibration
import os

class CalibrateWidget(QWidget):
    """
    标定窗口，将引导机器人运动，并提示操作人员拍照
    """
    def __init__(self):
        super(CalibrateWidget, self).__init__()
        self.initUI()

    def initUI(self):
        self.autoBtn = QPushButton(self.tr('Auto\n Calibration'))
        self.autoBtn.setFixedSize(80,80)
        self.autoBtn.setDisabled(True)
        self.nextPosBtn = QPushButton(self.tr('Next\n Position'))
        self.nextPosBtn.setFixedSize(80,80)
        self.nextPosBtn.setDisabled(True)
        self.captureBtn = QPushButton(self.tr('Capture'))
        self.captureBtn.setFixedSize(80,80)
        self.captureBtn.setDisabled(True)


        layout = QHBoxLayout()
        layout.addWidget(self.autoBtn)
        layout.addWidget(self.nextPosBtn)
        layout.addWidget(self.captureBtn)

        layout2 = QVBoxLayout()
        self.stateText = QTextEdit()
        self.stateText.setReadOnly(True)
        self.stateText.setText('Waiting for Robot.')
        layout2.addLayout(layout)
        layout2.addWidget(self.stateText)

        self.setLayout(layout2)

class Calibration(QThread):
    def __init__(self, cfg, parent):
        super(Calibration, self).__init__()
        self.cfg = cfg
        self.calibrateWidget = CalibrateWidget()
        self.calibrateWidget.hide()
        self.calibrateWidget.captureBtn.clicked.connect(self.slot_capture_btn)
        self.calibrateWidget.nextPosBtn.clicked.connect(self.slot_next_pos_btn)
        self.calibrateWidget.autoBtn.clicked.connect(self.slot_auto_btn)
        if os.path.exists('../CalibrationImages/pos.txt'):
            os.remove('../CalibrationImages/pos.txt')
        self.parent = parent
        self.robot = Robot(cfg)  # 与PLC通讯相关
        self.robot.start()
        self.robot.systemStateChange.connect(self.init_system_state_change)
        # 解析的机器人移动点为将会被保存到此处[p0, p1, ..., pn]
        # p0 = x, y, z, al, be, ga
        self.robotRealPos = [] # 真实末端位置（来自PLC）
        self.pos_cnt = 0 # 用于记录当前发送到哪一个点了
        self.pos_cnt_limit = 4 # 极限运动次数
        self.calibrateState = -1  # init初始化态： 检查网络并且等待Robot空闲
        self.is_calibrating_flag = False # 正在进行单次标定，用于阻塞不断允许标定的PLC通讯
        self.is_calibrate_done = False # 整体标定是否结束

    def show_text_state(self, txt):
        self.calibrateWidget.stateText.setText(txt)


    def slot_next_pos_btn(self):
        """
        按钮“next position btn”的响应函数.
        当还存在位置时，向机器人请求运动到新的位置.
        当所有位置运动完毕后，系统进入标定.
        :return:
        """
        if self.pos_cnt < self.pos_cnt_limit:
            self.show_text_state(f'Robot is moving to position: {self.pos_cnt+1} !\n\n\n'
                                 f'DO NOT PUSH'
                                 f' ANY BUTTON BEFORE ROBOT MOVE IS DONE.')
            self.robot.set_calibrate_req(self.pos_cnt)  # 发送标定请求
            self.robot.set_request_camera_calibrate('Calibrating')
        else:
            self.robot.set_request_camera_calibrate('Done')
            # 测试用，并没有实际进行最后的标定计算程序.
            self.calibrateState = 3
            self.show_text_state('Done!')
            print(self.robotRealPos)
            self.is_calibrate_done = True # 结束标定
            #calibration(self.robotRealPos)


    def slot_capture_btn(self):
        """
        保存图像，且此时才真正完成了一次采集，位置计数 pos_cnt + 1
        """
        cv2.imwrite(f'../CalibrationImages/Left-{self.pos_cnt}.bmp', self.parent.leftCamera.camera.capture())
        cv2.imwrite(f'../CalibrationImages/Right-{self.pos_cnt}.bmp', self.parent.rightCamera.camera.capture())
        self.pos_cnt += 1 #
        self.calibrateState = 1


    def slot_auto_btn(self):
        """
        自动化标定 SLOT函数
        """
        ret = QMessageBox.warning(self, self.tr('Warning!'),
                                  self.tr('Are you sure to calibrate automatically?'), QMessageBox.No, QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            pass

    def run(self):
        """
        标定时进入的核心死循环，所有状态都由PLC切换
        :return:
        """
        while True:
            if self.calibrateState == -1:  # 初始状态，检查网络
                # 只有PLC读取信号当机器人是空闲状态时才能离开此状态
                #LOG(log_types.NOTICE, self.tr('Waiting for Robot.'))
                #self.show_text_state('Waiting for Robot.')
                pass

            elif self.calibrateState == 0:  # 发送标定请求
                # 只有当机器人返回允许标定才能离开此状态
                self.robot.set_request_camera_calibrate('Request')  # 请求标定

            elif self.calibrateState == 1:  # 准备开始标定
                self.calibrateWidget.autoBtn.setEnabled(True)
                self.calibrateWidget.nextPosBtn.setEnabled(True)
                self.calibrateWidget.captureBtn.setDisabled(True)

            elif self.calibrateState == 3:  # 机器人正在移动中，禁用所有按钮动作
                self.calibrateWidget.nextPosBtn.setDisabled(True)
                self.calibrateWidget.captureBtn.setDisabled(True)

            elif self.calibrateState == 2: # 机械臂移动到位
                self.calibrateWidget.captureBtn.setEnabled(True)
                self.calibrateWidget.nextPosBtn.setDisabled(True)



    def init_system_state_change(self, state, datalst):
        """
        通过Robot的响应函数，激发此函数，导致系统的状态发生改变.
        :param state:
        :param datalst:  数据列表
        :return:
        """
        print('in state! ', state)
        if state == 0x10 and not self.is_calibrating_flag and not self.is_calibrate_done:
            # PLC命令解析：读取到机器人空闲--> 准备请求标定
            self.calibrateState = 0
            self.show_text_state('Request Robot to calibrate.')
        elif state == 0x11 and not self.is_calibrating_flag and not self.is_calibrate_done:
            # PLC允许标定 且 当前系统没有处在标定中状态(过滤PLC不断发送允许指令)
            self.show_text_state('Robot is ready to calibrate.')
            self.calibrateState = 1 # 界面按钮刷新: 允许next pos btn, 但静止拍照
            self.is_calibrating_flag = True
        elif state == 0x12:
            # PLC已经接收到运动指令，机械臂正在运动中
            self.calibrateState = 3
        else:
            # 机械臂到位
            if state - 0x100 == self.pos_cnt and self.is_calibrating_flag:
                # 注意！这里使用了pos_cnt与送来的指令做比较，以确保通讯合法
                # 注意！ 只有当当前次系统正在标定，才能够进入，过滤PLC不断发送“机器人到达位置”
                self.calibrateState = 2
                # 关闭Text State的Read Only， 写入新的状态
                self.show_text_state(f'Robot has been moved to pos{self.pos_cnt},{datalst[0]},{datalst[1]},{datalst[2]}.')
                path = 'C:/Users/001/Desktop/code/ContinousCastingVisionSystem/CalibrationImages'
                with open(path+f'/pos-{self.pos_cnt}.txt', 'w') as f:
                    for data in datalst:
                        f.write(str(data)+',')
                    f.write('\n')
                    f.close()
                self.robotRealPos.append(datalst)
                self.is_calibrating_flag = False


import numpy as np
if __name__ == '__main__':
    # 离线标定
    pos_file = '../CalibrationImages/pos.txt'
    if os.path.exists(pos_file):
        with open('../CalibrationImages/pos.txt', 'r') as f:
            lines = f.readlines()
            lines = [np.array(x.split(',')[:-1], np.float32).reshape(1, -1) for x in lines]
            calibration(lines)