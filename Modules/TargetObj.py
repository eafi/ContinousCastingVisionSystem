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
    def __init__(self, rect,trans):
        """
        :param rect: 第一次检测到的rect，用于判断机械臂是否在运动
        :param trans: 用于保存估计得到的目标变换矩阵，可能是list也可能是单个矩阵
        """
        self.momentum = deque(maxlen=20)
        self.momentum.append(rect)
        self.isStable = False

        self.trans = deque(maxlen=20)
        self.trans.append(trans)


    def step(self, rect, trans):
        """
        刷新目标坐标
        :return:
        """
        self.momentum.append(rect)
        self.trans.append(trans)
        if np.var(self.momentum) < 0.01:
            # 标定板静止
            self.isStable = True
        else:
            self.isStable = False


    def avg(self):
        if self.isStable:
            m = np.mean(self.trans, axis=0)
            return m
        # 标定板正在运动，不能返回
        return None



