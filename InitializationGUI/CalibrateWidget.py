from PyQt5.QtWidgets import QWidget, QMessageBox, QPushButton, QHBoxLayout, QTextEdit, QVBoxLayout
from Modules.Robot import Robot
from Modules.LOG import *
import cv2
from PyQt5.QtCore import QThread
from Modules.calibration import calibration
import os

class CalibrateWidget(QWidget):
    def __init__(self):
        super(CalibrateWidget, self).__init__()
        self.initUI()

    def initUI(self):
        self.nextPosBtn = QPushButton(self.tr('Next\n Position'))
        self.nextPosBtn.setFixedSize(80,80)
        self.nextPosBtn.setDisabled(True)
        self.captureBtn = QPushButton(self.tr('Capture'))
        self.captureBtn.setFixedSize(80,80)
        self.captureBtn.setDisabled(True)


        layout = QHBoxLayout()
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
        if os.path.exists('../CalibrationImages/pos.txt'):
            os.remove('../CalibrationImages/pos.txt')
        self.parent = parent
        self.robot = Robot(cfg)
        self.robot.start()
        self.robot.systemStateChange.connect(self.init_system_state_change)
        # 解析的机器人移动点为将会被保存到此处[p0, p1, ..., pn]
        # p0 = x, y, z, al, be, ga
        self.robotMovePos = []
        self.robotRealPos = [] # 真实末端位置（来自PLC）
        self.parse_robot_move_pos_to_list()
        self.posCnt = 0 # 用于记录当前发送到哪一个点了
        self.calibrateState = -1  # init初始化态： 检查网络并且等待Robot空闲


    def show_text_state(self, txt):
        self.calibrateWidget.stateText.setText(txt)
        pass


    def slot_next_pos_btn(self):
        if self.posCnt < len(self.robotMovePos):
            self.show_text_state(f'Robot is moving to pos{self.posCnt}')
            self.robot.set_move_vec(self.robotMovePos[self.posCnt])
            self.robot.set_calibrate_req(self.posCnt)  # 发送标定请求
            self.robot.set_request_camera_calibrate('Calibrating')
        else:
            calibration(self.robotRealPos)


    def slot_capture_btn(self):
        cv2.imwrite(f'../CalibrationImages/Left-{self.posCnt}.png', self.parent.leftCamera.im_np)
        cv2.imwrite(f'../CalibrationImages/Right-{self.posCnt}.png', self.parent.rightCamera.im_np)
        self.posCnt += 1
        self.calibrateState = 1

    def run(self):
        while True:
            if self.calibrateState == -1:  # 初始状态，检查网络
                # 只有当机器人是空闲状态时才能离开此状态
                LOG(log_types.NOTICE, self.tr('Waiting for Robot.'))
                #self.show_text_state('Waiting for Robot.')

            elif self.calibrateState == 0:  # 发送标定请求
                # 只有当机器人返回允许标定才能离开此状态
                self.robot.set_request_camera_calibrate('Request')  # 请求标定

            elif self.calibrateState == 1:  # 准备开始标定
                self.calibrateWidget.nextPosBtn.setEnabled(True)
                self.calibrateWidget.captureBtn.setDisabled(True)

            elif self.calibrateState == 2: # 机械臂移动到位
                self.calibrateWidget.captureBtn.setDisabled(False)
                self.calibrateWidget.nextPosBtn.setDisabled(True)



    def init_system_state_change(self, state, datalst):
        print('in state! ', state)
        if state == 0x10:
            # 机器人空闲--> 准备请求标定
            self.calibrateState = 0
            self.show_text_state('Request Robot to calibrate.')
        elif state == 0x11:
            # 机器人标定允许 -->  准备开始标定
            self.show_text_state('Robot is ready to calibrate.')
            self.calibrateState = 1
        else:
            if state - 0x12 == self.posCnt: # 机械臂到位
                self.calibrateState = 2
                self.show_text_state(f'Robot moved to pos{self.posCnt},{datalst[0]},{datalst[1]},{datalst[2]}.')
                with open('../CalibrationImages/pos.txt', 'a') as f:
                    for data in datalst:
                        f.write(str(data)+',')
                    f.write('\n')
                    f.close()
                self.robotRealPos.append(datalst)

    def parse_robot_move_pos_to_list(self):
        movPosMap = self.cfg['HandEyeCalibration_Conf']
        for key in movPosMap:
            if 'RobotMovePos' in key:
                self.robotMovePos.append(movPosMap[key])

import numpy as np
if __name__ == '__main__':
    # 离线标定
    pos_file = '../CalibrationImages/pos.txt'
    if os.path.exists(pos_file):
        with open('../CalibrationImages/pos.txt', 'r') as f:
            lines = f.readlines()
            lines = [np.array(x.split(',')[:-1], np.float32).reshape(1, -1) for x in lines]
            calibration(lines)