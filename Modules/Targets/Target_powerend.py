from Modules.Target import Target
import numpy as np
from Modules.utils import *
class Target_powerend(Target):
    """
    能源介质街头安装与卸载的目标文件
    1. 默认使用上ROI(提供X、和eular_X)进行安装，
    2. 默认使用上ROI(提供X, eular_X)进行卸载.
    3. 最终计算的Y轴使用拟合圆进行修正，拟合参数在CONF.cfg-TargetCircle_Conf-PowerEndCircle
    """
    def __init__(self, cfg):
        super(Target_powerend, self).__init__(
            cfg=cfg, tar_name='PowerEnd', roi_names=['TopROI'])


    def target_estimation(self, mtx: np.ndarray,
                          dist: np.ndarray,
                          cam2base: np.ndarray,
                          rects,
                          state):

        """
        目标估计: 根据标定板的物理尺度进行PnP计算, 然后根据CFG刚体矩阵转换到目标抓取位置，最后根据手眼标定矩阵转换到机器人坐标系
        :param rects: 字典
        :return: X Y Z eular_x eular_y eular_z
        """
        tar2board = self.cfg['Tar2Board_Conf']['TopROIPowerEndTar2Board']
        xyzrpy = None
        if state == 'Install' and 'TopROI' in rects.keys():
            board2cam = self.transform_board_2_camera(mtx, dist, rects['TopROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            xyzrpy = trans2xyzrpy(tar2base)
            xyzrpy[3] += 180.0 - 45.0 # 角度经验修正
            xyzrpy[0] -= 10.08 # 末端安装位向水口安装板法兰中心x向经验修正量
            xyzrpy[1] = self.intersection(xyzrpy[0]) # 环形修正
        elif state == 'Remove' and 'TopROI' in rects.keys():
            """
            rect[0]: 左标定板, 提供x, y方向
            rect[1]: 下标定板，提供角度
            """
            board2cam = self.transform_board_2_camera(mtx, dist, rects['TopROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            xyzrpy = trans2xyzrpy(tar2base)
            xyzrpy[3] += 180.0 # 角度经验修正
            xyzrpy[0] -= 10.08 # 末端安装位向水口安装板法兰中心x向经验修正量
            xyzrpy[1] = self.intersection(xyzrpy[0]) # 环形修正
        return xyzrpy


    def intersection(self, x):
        """
        水口安装板，水口安装末端位在旋转实验台圆心位置所绘制的圆形。
        利用该先验圆形提供机器人基坐标系下y轴深度补偿
        :param x: 由PnP计算得到的机器人基坐标系下的x坐标
        :param xc:
        :param yc:
        :param rc:
        :return:
        """
        circle_conf = self.cfg['TargetCircle_Conf']['NozzleCircle']
        xc = circle_conf[0]
        yc = circle_conf[1]
        rc = circle_conf[2]
        return np.sqrt(rc*rc - (xc-x)*(xc-x)) + yc

