"""
=================
Author: Yifei Zhang
Email: imeafi@gmail.com

TargetObj用于描述检测到的目标对象。一旦监测系统检测到对象后，将分配一个TargetObj用于记录：
1. 发现的所有坐标列表

并对整个系统提供如下信息：
1. 对象的运动、静止状态
2. 返回求平均后的目标位置
"""
from PyQt5.QtCore import QObject
import numpy as np
from collections import deque


class TargetObj(QObject):
    def __init__(self, m):
        """
        :param trans: 第一次检测到的偏移量
        :param eular: 第一次检测到的Eular转角
        """
        self.momentum = deque(maxlen=10)
        self.momentum.append(m)
        self.isStable = False


    def step(self, m):
        """
        刷新目标坐标
        :return:
        """
        if np.linalg.norm(m-self.momentum[0], ord=1) < 0.5:
            # 标定板静止
            self.isStable = True
        else:
            self.isStable = False
        self.momentum.append((m))


    def avg(self):
        if self.isStable:
            m = np.mean(self.momentum, axis=0)
            return m
        # 标定板正在运动，不能返回
        return None



