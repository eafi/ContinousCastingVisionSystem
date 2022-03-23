"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

Robot文件提供了对机械臂的概念抽象，提供：
1. 机械臂状态维护（当前空间状态、可动状态等）
2. 发送运动到指定目标的指令
3. 检查机器人的状态
"""
from PyQt5.QtCore import QObject
from Modules.network import Network
from Modules.LOG import *
from scipy.spatial.transform import Rotation as R
import numpy as np


class Robot(QObject):
    def __init__(self, cfg):
        super(Robot, self).__init__()
        self.cfg = cfg
        self.ip = cfg['Network_Conf']['IP']
        self.port = cfg['Network_Conf']['PORT']
        self.network = Network(ip=self.ip, port=self.port)
        self.network.start()


    def move(self, transMat):
        """
        机器人运动到目标位置
        :param transMat: 转换矩阵
        :return:
        """
        ctl = self.cfg['Network_Conf']['NetworkRequestMove']
        # 从转换矩阵到向量： x y z - eular_x - eular_y - eular_z
        eular = R.from_matrix(transMat[:3, :3]).as_euler('xyz', degrees=True)  # 外旋角度制
        trans = transMat[:3, 3]
        data = 9 * [np.float32(0.0)]
        data[:3] = trans
        data[4:-3] = eular
        print(trans, eular, data)
        self.network.send(ctl, data)


    def check_robot_states(self):
        """
        询问机器人状态
        :return:
        """
        ctl = self.cfg['Network_Conf']['NetworkRequestRobotState']
        self.network.send(ctl)
        # 阻塞，等待传回机器人的姿态或者状态
        #res, pos = self.network.recv()

    def say_ok(self):
        ctl = self.cfg['Network_Conf']['NetworkOK']
        self.network.send(ctl)


    def say_error(self):
        ctl = self.cfg['Network_Conf']['NetworkError']
        self.network.send(ctl)




#if __name__ == '__main__':
#    from PyQt5.QtWidgets import QApplication
#    import sys
#    app = QApplication(sys.argv)
#    cfg = {
#        'Network_Conf' : {'IP':'127.0.0.1', 'PORT':6666}
#    }
#    r = Robot(cfg)
#    sys.exit(app.exec())
