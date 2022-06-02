from Modules.Target import Target
import numpy as np
from Modules.utils import *
class Target_nozzle(Target):
    """
    长水口安装与卸载的目标文件
    1. 长水口默认使用左ROI(提供X、和eular_X)进行安装，
    2. 长水口默认使用左ROI(提供X)和下ROI(eular_X)进行卸载.
    3. 长水口最终计算的Y轴使用拟合圆进行修正，拟合参数在CONF.cfg-TargetCircle_Conf-NozzleCircle
    """
    def __init__(self, cfg):
        super(Target_nozzle, self).__init__(
            cfg=cfg, tar_name='Nozzle', roi_names=['LeftROI', 'BottomROI'])


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
        tar2board = self.cfg['Tar2Board_Conf']['LeftROINozzleTar2Board']
        xyzrpy = None
        if state == 'Install' and 'LeftROI' in rects.keys():
            board2cam = self.transform_board_2_camera(mtx, dist, rects['LeftROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            self.compensation(Dx=-10.08, Dy='Circle', Dalpha=180.0-45.0)
        elif state == 'Remove' and 'LeftROI' in rects.keys() and 'BottomROI' in rects.keys():
            """
            rect[0]: 左标定板, 提供x, y方向
            rect[1]: 下标定板，提供角度
            """
            board2cam = self.transform_board_2_camera(mtx, dist, rects['LeftROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            self.compensation(Dx=-10.08, Dy='Circle')

            board2cam = self.transform_board_2_camera(mtx, dist, rects['BottomROI']) # 下标定板
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.compensation(Dalpha=trans2xyzrpy(tar2base)[3]+180.0)
        return self.xyzrpy

