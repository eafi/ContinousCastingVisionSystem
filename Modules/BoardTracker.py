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
from Modules.utils import *


class BoardTracker(QObject):
    def __init__(self, rect, roi_name):
        """
        :param rect: 第一次检测到的rect，用于判断机械臂是否在运动
        :param roi_name: e.g. LeftCameraLeftROI,将会根据左右相机读取指定相机参数、手眼参数
        """
        self.rects = deque(maxlen=3)
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
        if err < 0.15 and len(self.rects) == self.rects.maxlen:
            # 标定板静止
            self.isStable = True
            print(self.roi_name, 'Stable============================================')
        else:
            print(self.roi_name, 'No Stable============================================')
            self.isStable = False


    def fetch_stable_rect(self):
        if self.isStable:
            return np.mean(self.rects, axis=0)
        # 标定板正在运动，不能返回
        else:
            return None


if __name__ == '__main__':
    from parse import CfgManager
    cfg = CfgManager('../CONF.cfg').cfg
    #src_img = 'C:/Users/xjtu/Downloads/Compressed/LeftCamera-228/right.png'
    src_img = 'C:/Users/001/Desktop/imgs/0.bmp'
    src_img = cv2.imread(src_img, cv2.IMREAD_GRAYSCALE)
    ms = []
    for dx, cam in zip([300, 1600], ['Left', 'Right']):
        dh = 700 # ROI的垂直偏移
        img = src_img[dh:dh+768, dx:dx+768]
        cv2.imshow('img', img)
        cv2.waitKey(0)
        from Detection_1.search import search
        rect = search(img, roi_size=0, ring_threshold=[0, 1.0, 0.1])
        roi_name = f'LeftCamera{cam}ROI'
        # 注意，单元测试时，需要把ROI返还回全局相机成像平面坐标系下
        bgr_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        cv2.line(bgr_img, rect[0].astype(np.int32), rect[1].astype(np.int32), (0, 0, 255), 2)
        cv2.line(bgr_img, rect[1].astype(np.int32), rect[2].astype(np.int32), (0, 0, 255), 2)
        cv2.line(bgr_img, rect[2].astype(np.int32), rect[3].astype(np.int32), (0, 0, 255), 2)
        cv2.line(bgr_img, rect[3].astype(np.int32), rect[0].astype(np.int32), (0, 0, 255), 2)
        cv2.imshow('found', bgr_img)
        cv2.waitKey(0)
        rect = rect + np.array((dx, dh))
        print(rect)
        tracker = ObjTracker(rect=rect, roi_name=roi_name, cfg=cfg)

        cnt = 0
        while True:
            tracker.step(rect)
            m = tracker.fetch_posture()
            if m is not None:
                ms.append(m[0])
                print(m[0])
                #np.save('right_camera_left_roi.npy', m)
                break
    print(ms[0][0,3])
    print(ms[0][1,3])
    ms[0][0,3] -= 10.08
    ms[0][1,3] = intersection(ms[0][0, 3])
    #delta = np.array([3.26228868,-20.28696512,0.83168597])
    #delta = np.array([3.26228868,-20.28696512,0.83168597])
    #delta = np.array([-0.80293111,-12.46166009, -0.20752269])

    #print(np.linalg.norm(ms[0][:3, 3]-ms[1][:3, 3], ord=2))
    #ms[1][:3, 3] += delta
    #print(np.linalg.norm(ms[0][:3, 3]-ms[1][:3, 3], ord=2))
    #delta = ms[0][:3, 3]-ms[1][:3, 3]
    #print(delta)

    #from utils import trans2vecs
    #data = trans2vecs(ms[0])
    #eular = np.array([-17.59, 14.97, 89.83])
    #delta_eular = eular - data[3:]
    #print(delta_eular)



    # 利用矩阵乘法，直接计算出刚体的安装位置到标定板的关系
    #tar2base = np.array([-80.87, -3237.35, 176.91, -19.96, 14.94, 89.85])
    #from scipy.spatial.transform import Rotation as R
    #eular = R.from_euler('ZYX', tar2base[3:],  degrees=True)
    #tar2base_44 = np.zeros((4,4))
    #tar2base_44[:3 ,:3] = eular.as_matrix()
    #tar2base_44[:3, 3] = tar2base[:3].T
    #tar2base_44[3,3] = 1.0

    #board2base = ms[0]
    #base2board = np.linalg.inv(board2base)

    #tar2board = (base2board @ tar2base_44)

    #tar2board = np.load('../long_nozzle_left_tar2board_44.npy')
    #print(trans2vecs(tar2board))

    #print(trans2vecs(m))
    from Modules.Robot import Robot
    from Modules.parse import CfgManager
    cfgManager = CfgManager(path='../CONF.cfg')
    cfg = cfgManager.cfg
    ###degree = ms[0] @ tar2board # 角度

    pos = trans2vecs(ms[0])
    pos[2] += -376.1
    pos[3] += 180 - 45.0
    robot = Robot(cfg=cfg)
    robot.start()  # 不停发送系统状态
    while True:
        print(pos)
        robot.set_move_vec(pos)
        robot.set_system_mode(2)