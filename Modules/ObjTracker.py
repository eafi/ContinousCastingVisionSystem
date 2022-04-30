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
import glob
import sys

import cv2
from PyQt5.QtCore import QObject
import numpy as np
from collections import deque
from Modules.Detection_1.utils.PnP import *
from Modules.utils import vecs2trans


class ObjTracker(QObject):
    def __init__(self, cfg, rect, roi_name):
        """
        :param rect: 第一次检测到的rect，用于判断机械臂是否在运动
        :param roi_name: e.g. LeftCameraLeftROI
        """
        self.rects = deque(maxlen=10)
        self.rects.append(rect)
        self.isStable = False
        self.roi_name = roi_name
        self.cfg = cfg

        #读取必要转换文件: 相机内参数、畸变参数和手眼标定结果
        lr_name = roi_name.split('Camera')[0]
        self.mtx = self.cfg['Calibration_Conf'][f'{lr_name}CameraMatrix']
        self.dist = self.cfg['Calibration_Conf'][f'{lr_name}CameraDist']
        self.camera2base = self.cfg['Calibration_Conf'][f'{lr_name}HandEyeMatrix']



    def step(self, rect):
        """
        刷新目标坐标
        :return:
        """
        self.rects.append(rect)
        err = np.sum(np.var(self.rects, axis=0))
        print('curr error: ', err)
        if err < 0.15 and len(self.rects) == self.rects.maxlen:
            # 标定板静止
            self.isStable = True
            print(self.roi_name, 'Stable============================================')
        else:
            print(self.roi_name, 'No Stable============================================')
            self.isStable = False


    def fetch_posture(self):
        if self.isStable:
            m = self._target_estimation(self.roi_name, np.mean(self.rects, axis=0))
            #m = np.random.rand(4,2)
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
            tar2board = []
            tar2board.append(self.cfg['Tar2Board_Conf'][whichTarget + '1'])
            tar2board.append(self.cfg['Tar2Board_Conf'][whichTarget + '2'])
        else:
            tar2board = self.cfg['Tar2Board_Conf'][whichTarget]
        # 目标板已知绝对物理尺寸(在目标板左上角圆心为原点的坐标系下)

        # 判别标定板是横向还是竖向： 注意rect返回的 0-x, 1-y
        dw = rect[1][0] - rect[0][0]  # 宽度
        dh = rect[-1][1] - rect[0][1]  # 高度
        print(rect)
        # 确定是横向还是纵向标定板
        rectPtsRef = get_four_points(vertical=True) if dh > dw else get_four_points(vertical=False)

        # ==================== PNP 得到目标板在相机坐标系下 ======================
        ret, rvec, tvec = cv2.solvePnP(rectPtsRef, rect, self.mtx, self.dist)

        board2camera = vecs2trans(rvec=rvec, tvec=tvec)


        if isinstance(tar2board, list):
            tar2base = []
            tar2base.append(self.camera2base @ board2camera @ tar2board[0])
            tar2base.append(self.camera2base @ board2camera @ tar2board[1])
        else:
            tar2base = self.camera2base @ board2camera @ tar2board

        return tar2base


if __name__ == '__main__':
    from parse import CfgManager
    cfg = CfgManager('../CONF.cfg').cfg
    img = 'C:/Users/xjtu/Downloads/Compressed/LeftCamera-228'
    img = glob.glob(img+'/*.png')[0]
    img = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    img = img[800:800+768, 2560-768:]
    cv2.imshow('img', img)
    cv2.waitKey(0)
    from Detection_1.search import search
    rect = search(img, roi_size=0)
    roi_name = 'LeftCameraTopROI'
    # 注意，单元测试时，需要把ROI返还回全局相机成像平面坐标系下
    rect = rect + np.array((2560-768, 800))
    print(rect)
    tracker = ObjTracker(rect=rect, roi_name=roi_name, cfg=cfg)

    cnt = 0
    while True:
        tracker.step(rect)
        m = tracker.fetch_posture()
        if m is not None:
            print(m)
            break

