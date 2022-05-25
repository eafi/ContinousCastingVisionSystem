from Modules.Target import Target
import numpy as np
from Modules.utils import *
class Target_nozzle(Target):
    def __init__(self, cfg):
        super(Target_nozzle, self).__init__(
            cfg=cfg, tar_name='Nozzle', roi_names=['LeftROI', 'DownROI'])


    def target_estimation(self, mtx: np.ndarray,
                          dist: np.ndarray,
                          cam2base: np.ndarray,
                          rect):

        """
        目标估计: 根据标定板的物理尺度进行PnP计算, 然后根据CFG刚体矩阵转换到目标抓取位置，最后根据手眼标定矩阵转换到机器人坐标系
        :param rect:
        :return: X Y Z eular_x eular_y eular_z
        """
        super(Target_nozzle, self).target_estimation(mtx, dist,cam2base,rect)
        tar2board = self.cfg['Tar2Board_Conf']['LeftROINozzleTar2Board']
        if not self.is_installed():
            board2cam = self.pnp(mtx, dist, rect)
            tar2base = cam2base @ board2cam @ tar2board
            xyzrpy = trans2xyzrpy(tar2base)
            xyzrpy[3] += 180.0 - 45.0 # 角度经验修正
            xyzrpy[0] -= 10.08 # 末端安装位向水口安装板法兰中心x向经验修正量
            xyzrpy[1] = self.intersection(xyzrpy[0]) # 环形修正
            return xyzrpy
        else:
            """
            rect[0]: 左标定板, 提供x, y方向
            rect[1]: 下标定板，提供角度
            """
            board2cam = self.pnp(mtx, dist, rect[0])
            tar2base = cam2base @ board2cam @ tar2board
            xyzrpy = trans2xyzrpy(tar2base)
            xyzrpy[0] -= 10.08 # 末端安装位向水口安装板法兰中心x向经验修正量
            xyzrpy[1] = self.intersection(xyzrpy[0]) # 环形修正

            board2cam = self.pnp(mtx, dist, rect[1]) # 下标定板
            tar2base = cam2base @ board2cam @ tar2board
            xyzrpy[3] = trans2xyzrpy(tar2base)[3] + 180.0 # 角度正对下标定板
            return xyzrpy


    def intersection(self, x, xc=-173.79198, yc=-5005.76502, rc=1764.43751):
        """
        水口安装板，水口安装末端位在旋转实验台圆心位置所绘制的圆形。
        利用该先验圆形提供机器人基坐标系下y轴深度补偿
        :param x: 由PnP计算得到的机器人基坐标系下的x坐标
        :param xc:
        :param yc:
        :param rc:
        :return:
        """
        return np.sqrt(rc*rc - (xc-x)*(xc-x)) + yc

