from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from Modules.network import Network
from time import sleep
from Modules.utils import trans2xyzrpy
class Robot(QThread):
    systemStateChange = pyqtSignal(int, list) #在system.py 和 calibratewidget.py绑定
    #robotStateChange = pyqtSignal(list) # 标定时需要获得机械臂末端位置
    def __init__(self, cfg):
        super(Robot, self).__init__()
        self.cfg = cfg
        self.sendCtlBit = np.uint32(0)
        self.sendData = 6 * [np.float32(0.0)]
        self.sendResBit = [np.float32(0.0), np.float32(0.0), np.uint32(0)]

        self.recCtlBit = None
        self.recData = None
        self.recResBit = None

        self.network = Network(ip=self.cfg['Network_Conf']['IP'], port=self.cfg['Network_Conf']['PORT'])
        self.network.start()


    def set_left_camera(self, state):
        """
        受到CoreSystemMain.py中对应cameraWidget的statechange控制
        自动调用
        :param state:
        :return:
        """
        if state == 'OK':
            self.sendCtlBit |= self.cfg['Network_Conf']['NetworkLCameraOK']
        else:
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkLCameraOK']

    def set_right_camera(self, state):
        """
        自动调用
        :param state:
        :return:
        """
        if state == 'OK':
            self.sendCtlBit |= self.cfg['Network_Conf']['NetworkRCameraOK']
        else:
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkRCameraOK']

    def set_request_camera_calibrate(self, state='Done'):
        """
        设置标定状态，只能是三种状态中的一个
        :param state:
        :return:
        """
        # 清空之前的标定状态
        self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkCalibrateDone']
        if state == 'Request':
            self.sendCtlBit |= self.cfg['Network_Conf']['NetworkRequestCalibrate']
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkCalibrating']
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkCalibrateDone']
        elif state == 'Calibrating':
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkRequestCalibrate']
            self.sendCtlBit |= self.cfg['Network_Conf']['NetworkCalibrating']
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkCalibrateDone']
        elif state == 'Done':
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkRequestCalibrate']
            self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkCalibrating']
            self.sendCtlBit |= self.cfg['Network_Conf']['NetworkCalibrateDone']

    def set_system_mode(self, state):
        """
        设置系统状态，只能是五种状态中的一个
        设置此状态意味着视觉系统在这个状态的坐标计算完毕
        :param state:
        :return:
        """
        if 1 <= state <= 7:
            self.sendCtlBit |= self.cfg['Network_Conf'][f'NetworkState{state}']

    def reset_system_mod(self):
        for i in range(1,8):
            self.sendCtlBit &= ~self.cfg['Network_Conf'][f'NetworkState{i}']


    def set_move_mat(self, transMat):
        self.sendData = trans2xyzrpy(transMat)

    def set_move_xyzrpy(self, vec):
        self.sendData = vec

    def reset_move(self):
        self.sendData = 6 * [np.float32(0.0)]

    def set_calibrate_req(self, state):
        """
        请求机械臂移动到指定标定位置,
        :param state: 第几次请求
        :return:
        """
        if 0 <= state < 32:
            self.sendResBit[2] = 0x01 << state


    def reset_calibrate_req(self):
        self.sendResBit[2] = 0x00


    def set_light_on(self):
        self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkLightOff']
        self.sendCtlBit |= self.cfg['Network_Conf']['NetworkLightOn']


    def set_light_off(self):
        self.sendCtlBit &= ~self.cfg['Network_Conf']['NetworkLightOn']
        self.sendCtlBit |= self.cfg['Network_Conf']['NetworkLightOff']



    def run(self):
        """
        不停发送系统状态
        :return:
        """
        while True:
            sleep(0.5)  # 注意如果没有这个，可能会导致缓存崩溃
            self.set_network_ok() # 只要在发送，就一定意味着网络OK
            self.network.send(self.sendCtlBit, self.sendData, self.sendResBit)
            self.cmds_handler(self.network.msgManager.recCtlBits, self.network.msgManager.recData, self.network.msgManager.recResBits)


    def cmds_handler(self, ctl, data, res):
        """
        网络通讯: 接受PLC命令
        :param ctl:
        :param data:
        :param res:
        :return:
        """
        # 重复指令检查
        #print('dfsf', ctl)

        #if ctl == self.recCtlBit and data == self.recData and res == self.recResBit:
        #    return
        self.recCtlBit = ctl
        self.recData = data
        self.recResBit = res
        # =================== 核心计算状态切换和请求指令 ==================== #
        # PLC命令： 系统状态检查
        for state in range(1, 8):
            if ctl & self.cfg['Network_Conf'][f'NetworkState{state}']:
                self.systemStateChange.emit(state, [])

        # ==================  标定阶段: 接受状态切换以及读取姿态信息 =================== #
        # 检查机器人空闲
        if ctl & self.cfg['Network_Conf']['NetworkCanMove']:  # 注意请求运动和允许运动命令是镜像的
            self.systemStateChange.emit(0x10, [])

        # PLC命令： 标定允许
        if ctl & self.cfg['Network_Conf']['NetworkRequestCalibrateOK']:
            self.systemStateChange.emit(0x11, [])

        # PLC命令： PLC已经接收到运动指令，机械臂正在运动中，PLC请求 \
        #  清除系统发送当前Res冗余字位置[2] 为 0
        if ctl & self.cfg['Network_Conf']['NetworkOneStepCalibratingOK']:
            self.reset_calibrate_req()
            self.systemStateChange.emit(0x12, [])


        # PLC命令： 机器人到位，请拍照并准备下一个位置
        for state in range(32):
            if res[2] & (0x01 << state): # 注意不是控制位，而是Res[2]位置
                self.systemStateChange.emit(0x100+state, self.recData)


    #def get_plc_ok(self):
    #    """
    #    从PLC读取系统运行状态
    #    :return:
    #    """
    #    if self.recCtlBits & self.cfg['Network_Conf']['NetworkOK']:
    #        return True
    #    else:
    #        return False

    def set_network_ok(self):
        """
        告知PLC通讯正常
        :return:
        """
        self.sendCtlBit |= self.cfg['Network_Conf']['NetworkOK']

