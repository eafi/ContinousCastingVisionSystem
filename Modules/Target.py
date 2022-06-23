import numpy as np
import cv2

from Modules.utils import *

class Target:
    """
    各个目标物体的名字，保存其状态：安装？拆卸？姿态转换表等
    所有新的目标应该继承自本类，并且必须实现estimation方法，
    在coreSystem中，需要注册新目标，并叫目标加入指定的网络通讯State中。
    网络state的具体含义已经被预定义，并在CONF.cfg文件
    """
    def __init__(self, cfg, tar_name):
        """

        :param cfg:
        :param tar_name:
        :param roi_names: 与当前目标密切相关的ROI窗的名字
        """
        assert isinstance(tar_name, str)
        self.cfg = cfg
        self.tar_name = tar_name # 工件名字
        self.is_installed_flag = False
        self.xyzrpy = None
        self.state = 'Install'

    def done(self):
        """
        安装或者卸载完成了
        :return:
        """
        self.is_installed_flag = ~self.is_installed_flag


    def get_current_valid_roi_names(self, state):
        """
        安装或卸载时，target所需求的目标可能是不同的. 本函数根据安装或卸载，返回roi names.
        注意：返回必须为列表，且返回的内容必须为有意义的ROI, 比如 ['LeftROI']
        :param state: 目标状态
        """
        raise NotImplementedError


    def is_installed(self):
        return self.is_installed_flag

    def is_removed(self):
        return ~self.is_installed_flag

    def transform_board_2_camera(self, mtx, dist, rect: np.ndarray):
        dw = rect[1][0] - rect[0][0]  # 宽度
        dh = rect[-1][1] - rect[0][1]  # 高度
        # 确定是横向还是纵向标定板
        rectPtsRef = get_four_points(vertical=True) if dh > dw else get_four_points(vertical=False)

        # ==================== PNP 得到目标板在相机坐标系下 ======================
        ret, rvec, tvec = cv2.solvePnP(rectPtsRef, rect, mtx, dist, cv2.SOLVEPNP_IPPE)
        board2camera = cv2trans(rvec=rvec, tvec=tvec)
        return board2camera

    def transform_target_2_base(self, cam2base, board2cam, tar2board):
        tar2base = cam2base @ board2cam @ tar2board
        return tar2base

    def target_estimation(self,mtx: np.ndarray, dist: np.ndarray, cam2base: np.ndarray, rects: np.ndarray, state: str):
        """
        :param mtx:
        :param dist:
        :param hand:
        :param rect:
        :param state: Install or Remove
        :return:
        """
        self.state = state
        self.rects = rects
        self.xyzrpy = None

    def intersection(self, x, state=''):
        """
        水口安装板，水口安装末端位在旋转实验台圆心位置所绘制的圆形。
        利用该先验圆形提供机器人基坐标系下y轴深度补偿
        :param x: 由PnP计算得到的机器人基坐标系下的x坐标
        :param xc:
        :param yc:
        :param rc:
        :return:
        """
        circle_conf = self.cfg['TargetCircle_Conf'][f'{self.state}{self.tar_name}Circle']
        xc = circle_conf[0]
        yc = circle_conf[1]
        rc = circle_conf[2]
        return np.sqrt(rc*rc - (xc-x)*(xc-x)) + yc

    def compensation(self, Dx=0, Dy=0, Dz=0, Dalpha=0, Dbeta=0, Dgamma=0):
        print('Before Compensation:', self.xyzrpy)
        assert isinstance(Dx, (float, int))
        assert isinstance(Dy, (float, str, int))
        assert isinstance(Dz, (float, int))
        assert isinstance(Dalpha, (float, int))
        assert isinstance(Dbeta, (float, int))
        assert isinstance(Dgamma, (float, int))
        self.xyzrpy[0] += Dx
        if Dy == 'Circle':
            self.xyzrpy[1] = self.intersection(self.xyzrpy[0]) # 环形修正
        else:
            self.xyzrpy[1] += Dy
        self.xyzrpy[2] += Dz
        self.xyzrpy[3] += Dalpha
        self.xyzrpy[4] += Dbeta
        self.xyzrpy[5] += Dgamma


    def needed_roi_names(self, roi_names):
        if isinstance(roi_names, str):
            roi_names = [roi_names]
        assert isinstance(roi_names, list)
        for roi_name in roi_names:
            if roi_name not in self.rects.keys():
                return False
        return True



