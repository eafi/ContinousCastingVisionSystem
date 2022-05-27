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
    def __init__(self, cfg, tar_name, roi_names):
        """

        :param cfg:
        :param tar_name:
        :param roi_names: 与当前目标密切相关的ROI窗的名字
        """
        assert isinstance(tar_name, str)
        self.cfg = cfg
        self.tar_name = tar_name # 工件名字
        self.roi_names = roi_names
        self.is_installed_flag = False

    def done(self):
        """
        安装或者卸载完成了
        :return:
        """
        self.is_installed_flag = ~self.is_installed_flag


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
        raise NotImplementedError
