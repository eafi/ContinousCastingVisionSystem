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

class ROBOT_CTL_BITS:
    error = 1
    ok = 0

    # Request Command
    request_move = 2
    request_robot_state = 3

    # Get Command
    get_system_state = 4



class Robot(QObject):
    def __init__(self, ip, port):
        super(Robot, self).__init__()
        self.init(ip, port)

    def init(self, ip, port):
        """
        初始化机器人资源，尝试与PLC通讯
        :return:
        """
        try:
            self.network = Network(ip=ip, port=port)
            self.network.start()
        except Exception as e:
            LOG(log_types.FAIL, self.tr('Network init failed.'))
            print(e)


    def move(self, pos):
        """
        机器人运动到目标位置
        :param pos:
        :return:
        """
        ctl = ROBOT_CTL_BITS.request_move
        self.network.send(ctl, pos)


    def check_robot_states(self):
        """
        询问机器人状态
        :return:
        """
        ctl = ROBOT_CTL_BITS.request_robot_state
        self.network.send(ctl)
        # 阻塞，等待传回机器人的姿态或者状态
        res, pos = self.network.recv()

    def say_ok(self):
        ctl = ROBOT_CTL_BITS.ok
        self.network.send(ctl)


    def say_error(self):
        ctl = ROBOT_CTL_BITS.error
        self.network.send(ctl)

