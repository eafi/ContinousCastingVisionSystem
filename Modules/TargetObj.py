"""
=================
Author: Yifei Zhang
Email: imeafi@gmail.com

TargetObj用于描述检测到的目标对象。一旦监测系统检测到对象后，将分配一个TargetObj用于记录：
1. 发现的所有坐标列表

并对整个系统提供如下信息：
1. 对象的运动、静止状态
2. 优化检测对象函数的ROI，i.e. 缩小ROI区域
"""
from PyQt5.QtCore import QObject
import numpy as np
from collections import deque


class TargetObj(QObject):
    def __init__(self, rect: np.ndarray):
        """
        :param rect: 第一次检测到的位置
        """
        self.rects = deque(maxlen=10)
        self.rects.append(rect)


    def step(self, rect):
        """
        刷新目标坐标
        :param rect:
        :return:
        """
        if np.linalg.norm(rect-self.rects[-1], ord=1) < 0.01:
            print('Stable....')
        else:
            print('Moving...')
        self.rects.append(rect)

