from Modules.Target import Target
import numpy as np
from Modules.utils import *
class Target_slider(Target):
    def __init__(self, cfg):
        """滑板液压缸安装与卸载的目标文件
        1.默认使用水口安装版Left ROI(提供X、和eular_X)进行安装，
        2.默认使用Left ROI 和自身ROI(提供X和eular_X)进行卸载
        3.最终计算的Y轴使用拟合圆进行修正，拟合参数在CONF.cfg - TargetCircle_Conf - SliderCircle
        """
        super(Target_slider, self).__init__(
            cfg=cfg, tar_name='Slider', roi_names=['RightROI', 'TopROI'])



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
        tar2board = self.cfg['Tar2Board_Conf']['RightROISliderTar2Board']
        if state == 'Install' and 'RightROI' in rects.keys():
            board2cam = self.transform_board_2_camera(mtx, dist, rects['RightROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            self.compensation(
                Dx=-10,
                Dy='Circle',
                Dz=-80,
                Dalpha=140.0-1.0)

        elif state == 'Remove' and 'TopROI' in rects.keys() and 'RightROI' in rects.keys():
            """
            rect[0]: 左标定板, 提供x, y方向
            rect[1]: 下标定板，提供角度
            """
            board2cam = self.transform_board_2_camera(mtx, dist, rects['RightROI'])
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            self.xyzrpy = trans2xyzrpy(tar2base)
            #xyzrpy[1] = self.intersection(xyzrpy[0]) # 环形修正

            board2cam = self.transform_board_2_camera(mtx, dist, rects['TopROI']) # 提供角度`
            tar2base = self.transform_target_2_base(cam2base, board2cam, tar2board)
            #xyzrpy[3] = trans2xyzrpy(tar2base)[3] + 180.0 # 角度正对下标定板
        return self.xyzrpy



