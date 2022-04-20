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
from Modules.Detection_1.utils.PnP import *
from Modules.utils import vecs2trans


class TargetObj(QObject):
    def __init__(self, rect, roi_name):
        """
        :param rect: 第一次检测到的rect，用于判断机械臂是否在运动
        :param trans: 用于保存估计得到的目标变换矩阵，可能是list也可能是单个矩阵
        """
        self.rects = deque(maxlen=10)
        self.rects.append(rect)
        self.isStable = False

        self.roi_name = roi_name


    def step(self, rect):
        """
        刷新目标坐标
        :return:
        """
        self.rects.append(rect)
        err = np.sum(np.var(self.rects, axis=0))
        print('curr error: ', err)
        if err < 0.01:
            # 标定板静止
            self.isStable = True
            print(self.roi_name, 'Stable============================================')
        else:
            print(self.roi_name, 'No Stable============================================')
            self.isStable = False


    def fetch_posture(self):
        if self.isStable:
            #m = self._target_estimation(self.roi_name, np.mean(self.rects, axis=0))
            m = np.random.rand(4,2)
            return m
        # 标定板正在运动，不能返回
        return None



    def _target_estimation(self, whichCamerawhichROI: str, rect: np.ndarray):
        """
        目标估计: 根据标定板的物理尺度进行PnP计算, 然后根据CFG刚体矩阵转换到目标抓取位置，最后根据手眼标定矩阵转换到机器人坐标系
        :param whichCamerawichROI:
        :param rect:
        :return:
        如果该ROI是左右两个标定板区域，那么需要计算两个Target: 水口安装位置 + 滑动液压钢位置 , 返回list
        如果该ROI是其他区域，那么只返回一个矩阵即可
        """
        # 哪一个ROI区域，用于决定哪一个刚体目标
        whichTarget = whichCamerawhichROI.split('Camera')[1].replace('ROI', 'Ref')

        # 获得目标板到刚体目标的转换矩阵(在parse。py中已经转化成矩阵)
        if whichTarget == 'LeftRef' or whichTarget == 'RightRef':
            # 左右参考标定板代表了两个坐标：水口安装位置 + 滑板液压缸安装位置，因此需要保存两个矩阵
            rect2Target = []
            rect2Target.append(self.cfg['RectRef2Target_Conf'][whichTarget + '1'])
            rect2Target.append(self.cfg['RectRef2Target_Conf'][whichTarget + '2'])
        else:
            rect2Target = self.cfg['RectRef2Target_Conf'][whichTarget]
        # 目标板已知绝对物理尺寸(在目标板左上角圆心为原点的坐标系下)
        rectPtsRef = get_four_points()
        # 得到目标板在相机坐标系下
        imgpts, rvec, tvec = pnp(rect, objp=rectPtsRef)
        camera2rect = vecs2trans(rvec=rvec, tvec=tvec)

        robot2Camera = self.cfg['HandEyeCalibration_Conf']['HandEyeMatrix']

        if isinstance(rect2Target, list):
            robot2Target = []
            robot2Target.append(robot2Camera @ camera2rect @ rect2Target[0])
            robot2Target.append(robot2Camera @ camera2rect @ rect2Target[1])
        else:
            robot2Target = robot2Camera @ camera2rect @ rect2Target

        return robot2Target


if __name__ == '__main__':
    rect = np.random.rand(4,2) * 100
    tar = TargetObj(rect, 'LeftCameraLeftROI')
    from time import sleep
    while True:
        sleep(2)
        #rect = 100 * np.random.rand(4, 2)
        new_rect = rect + 0.01 * np.random.rand(4,2)
        print('new rect:',new_rect)
        tar.step(new_rect)

        m = tar.fetch_posture()
        if m is None:
            continue
        print(m)