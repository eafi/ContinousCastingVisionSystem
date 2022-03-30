from PyQt5.QtCore import QThread
import numpy as np
from Modules.network import Network
from Modules.utils import trans2vecs
class Robot(QThread):
    def __init__(self, cfg):
        self.robotRequestState = 0
        self.cfg = cfg
        self.ctlBit = np.uint32(0)
        self.data = 6 * [np.float32(0.0)]
        self.resBit = 3 * [np.uint32(0)]
        self.network = Network(ip=self.cfg['Network_Conf']['IP'], port=self.cfg['Network_Conf']['PORT'])
        self.network.start()
        self.network.msgManager.NetworkCmdSignal.connect(self.cmds_handler)


    def set_left_camera(self, state):
        """
        受到CoreSystemMain.py中对应cameraWidget的statechange控制
        自动调用
        :param state:
        :return:
        """
        if state == 'OK':
            self.ctlBit |= self.cfg['Network_Conf']['NetworkLCameraOK']
        else:
            self.ctlBit &= ~self.cfg['Network_Conf']['NetworkLCameraOK']

    def set_right_camera(self, state):
        """
        自动调用
        :param state:
        :return:
        """
        if state == 'OK':
            self.ctlBit |= self.cfg['Network_Conf']['NetworkRCameraOK']
        else:
            self.ctlBit &= ~self.cfg['Network_Conf']['NetworkRCameraOK']

    def set_request_camera_calibrate(self, state='Done'):
        """
        设置标定状态，只能是三种状态中的一个
        :param state:
        :return:
        """
        # 清空之前的标定状态
        self.ctlBit &= ~self.cfg['Network_Conf']['NetworkRequestCalibrate']
        self.ctlBit &= ~self.cfg['Network_Conf']['NetworkCalibrating']
        self.ctlBit &= ~self.cfg['Network_Conf']['NetworkCalibrateDone']
        if state == 'Request':
            self.ctlBit |= self.cfg['Network_Conf']['NetworkRequestCalibrate']
        elif state == 'Calibrating':
            self.ctlBit |= self.cfg['Network_Conf']['NetworkCalibrating']
        elif state == 'Done':
            self.ctlBit |= self.cfg['Network_Conf']['NetworkCalibrateDone']

    def set_system_mode(self, state):
        """
        设置系统状态，只能是五种状态中的一个
        设置此状态意味着视觉系统在这个状态的坐标计算完毕
        :param state:
        :return:
        """
        if 1 <= state <= 5:
            self.ctlBit |= self.cfg['Network_Conf'][f'NetworkState{state}']


    def set_move(self, transMat):
        self.data = trans2vecs(transMat)


    def set_calibrate_req(self, state):
        """
        请求机械臂移动到指定标定位置,
        :param state: 第几次请求
        :return:
        """
        if 0 <= state < 32:
            self.resBit[0] = 0x01 << state


    def cmds_handler(self, ctl, data, res):
        print('in cmds handler.')
        print(ctl)
        if ctl == 0x11:
            self.robotRequestState = 0x11
        elif ctl == 0x12:
            print('sdfsdf')
            self.robotRequestState = 0x12
        #elif ctl == 0x02: #  PLC允许机器人可以运动
        #    self.robot.canMove = True

    def run(self):
        """
        不停发送系统状态
        :return:
        """
        while True:
            self.set_network_ok() # 只要在发送，就一定意味着网络OK
            self.network.send(self.ctlBit, self.data, self.resBit)


    def get_plc_ok(self):
        """
        从PLC读取系统运行状态
        :return:
        """
        if self.recCtlBits & self.cfg['Network_Conf']['NetworkOK']:
            return True
        else:
            return False

    def set_network_ok(self):
        """
        告知PLC通讯正常
        :return:
        """
        self.sendCtlBits |= self.cfg['Network_Conf']['NetworkOK']

