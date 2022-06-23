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
            cfg=cfg, tar_name='PowerEnd')


    def get_current_valid_roi_names(self, state):
        if state == 'Install' or state == 'Remove':
            return ['TopROI']


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
        super(Target_powerend, self).target_estimation(mtx, dist, cam2base, rects, state)
        tar2board = self.cfg['Tar2Board_Conf']['TopROIPowerEndTar2Board']
        if state == 'Install' and self.needed_roi_names('TopROI'):
            board2cam = self.transform_board_2_camera(mtx, dist, rects['TopROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            self.compensation(Dx=-7.83, Dy='Circle', Dalpha=180-30-0.4)
        elif state == 'Remove' and self.needed_roi_names('TopROI'):
            """
            rect[0]: 左标定板, 提供x, y方向
            rect[1]: 下标定板，提供角度
            """
            board2cam = self.transform_board_2_camera(mtx, dist, rects['TopROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            self.compensation(Dx=-7.83, Dy='Circle', Dalpha=180 - 30 - 0.4)
        return self.xyzrpy



