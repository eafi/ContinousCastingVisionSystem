from PyQt5.QtWidgets import QWidget, QMessageBox
from Modules.Robot import Robot
import glob
from Modules.utils import vecs2trans
from Modules.LOG import *
import cv2
from Modules.calibration import camera_calibration, hand_eye_calibration
import numpy as np
from PyQt5.QtCore import QThread

class CalibrationWidget(QWidget):
    """
    联合标定： 相机标定 + 机械臂手眼标定. 需要提供机械臂末端的姿态信息
    :return:
    """
    def __init__(self, cfg, parent):
        super(CalibrationWidget, self).__init__()
        self.cfg = cfg
        self.calibrate = Calibrate(cfg)
        self.parent = parent


    def slot_init(self):
        """
        初始化标定，只在用户点击手眼标定后进行初始化工作
        :return:
        """
        warningStr='Do you want to recalibrate the arm and the vision system?\n' \
                   'You are supposed to do this process only if one of the followings happened:\n' \
                   '1. This is a brand new system and have not calibrate yet.\n' \
                   '2. The relative position between cameras and the arm has been changed.\n' \
                   '3. The focal length of cameras has been changed.\n' \
                   'Before you click YES button please make sure the chessboard has been right installed on the' \
                   'end of arm.\n\n\n' \
                   'WARNING: THE ARM WILL MOVE AUTOMATICALLY DURING CALIBRATION.'

        ret = QMessageBox.warning(self, self.tr('Warning!'),
                                  self.tr(warningStr), QMessageBox.No, QMessageBox.Yes)

        if ret == QMessageBox.Yes:
            if self.robot.network.connectSocket is None:
                LOG(log_types.NOTICE, self.tr('No Connection Yet.'))
                return
            self.calibrate.start()



class Calibrate(QThread):
    def __init__(self, cfg):
        super(Calibrate, self).__init__()

        self.robot = Robot(cfg)
        self.robot.start()
        self.robot.systemStateChange.connect(self.init_system_state_change)
        # 解析的机器人移动点为将会被保存到此处[p0, p1, ..., pn]
        # p0 = x, y, z, al, be, ga
        self.robotMovePos = []
        #self.parse_robot_move()
        self.posCnt = 0 # 用于记录当前发送到哪一个点了
        self.calibrateState = -1  # init初始化态： 检查网络并且等待Robot空闲
        pass

    def run(self):
        while True:
            if self.calibrateState == -1:  # 初始状态，检查网络
                LOG(log_types.NOTICE, self.tr('Waitting for Robot.'))

            elif self.calibrateState == 0:  # 发送标定请求
                print('reqeust to calibratin!!!')
                self.robot.set_request_camera_calibrate('Request')  # 请求标定

            elif self.calibrateState == 1:  # 准备开始标定
                self.robot.set_move(self.robotMovePos[self.posCnt])
                self.robot.set_calibrate_req(self.posCnt)  # 发送标定请求
                self.robot.set_request_camera_calibrate('Calibrating')

    def init_system_state_change(self, state):
        print('in state! ', state)
        if state == 0x10:
            # 机器人空闲--> 准备请求标定
            self.calibrateState = 0
        elif state == 0x11:
            # 机器人标定允许 -->  准备开始标定
            self.calibrateState = 1
        else:
            if state - 0x12 == self.posCnt: # 机械臂到位
                cv2.imwrite(f'../CalibrationImages/Left-{self.posCnt}.png', self.parent.leftCamera.im_np)
                cv2.imwrite(f'../CalibrationImages/Right-{self.posCnt}.png', self.parent.rightCamera.im_np)
                self.posCnt += 1
