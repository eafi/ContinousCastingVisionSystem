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

class Robot(QObject):
    def __init__(self):
        super(Robot, self).__init__()
        self.network = Network(ip='localhost', port=6667)
        self.network.start()


    def move_2_pos(self, pos):
        """
        机器人运动到目标位置
        :param pos:
        :return:
        """
        raise NotImplementedError


    def is_movable(self):
        """
        询问机器人是否可动
        :return:
        """
        raise NotImplementedError


    def check_robot_states(self):
        """
        询问机器人状态
        :return:
        """
        raise NotImplementedError
