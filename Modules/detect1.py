"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

detect1.py文件提供了Detection_1方法的Qt封装，以Qthread的形式向CoreSystem提供核心检测方法支持
"""
from PyQt5.QtCore import QThread, pyqtSignal
from Modules.LOG import *
from Modules.Detection_1.search import search
from Modules.Detection_1.utils.PnP import *
import numpy as np
import cv2


class Detection1(QThread):
    returnValSignal = pyqtSignal(str, np.ndarray)
    def __init__(self, cfg, description: str, img):
        super(Detection1, self).__init__()
        self.cfg = cfg
        self.img = img
        self.descriotion = description  # 用于描述这个img
        self.kargs = {}
        self.parse_cfg()

    def parse_cfg(self):
        assert 'Detection1_Conf' in self.cfg, LOG(log_types.FAIL,
                                                  self.tr('Cannot find Detection1 method configuration'))

        # 对每一个参数进行解析, 对val转换成指定格式
        args = self.cfg['Detection1_Conf']
        # 单参数
        self.kargs['roi_size'] = int(args['roi_size'])
        self.kargs['epsilon_k'] = float(args['epsilon_k'])
        self.kargs['epsilon_dst'] = float(args['epsilon_dst'])
        self.kargs['pts_type'] = (args['pts_type'])

        # 列表参数
        board_size_range = [int(x) for x in args['board_size_range'].split(',')]
        self.kargs['board_size_range'] = board_size_range
        ring_threshold = [float(x) for x in args['ring_threshold'].split(',')]
        self.kargs['ring_threshold'] = ring_threshold

        # tuple 参数
        self.kargs['kernel_size'] = tuple([int(x) for x in args['kernel_size'].split(',')])
        self.kargs['outer_diameter_range'] = tuple([int(x) for x in args['outer_diameter_range'].split(',')])
        self.kargs['ring_width_range'] = tuple([int(x) for x in args['ring_width_range'].split(',')])
        self.kargs['area_threshold'] = tuple([int(x) for x in args['area_threshold'].split(',')])



    #def run(self):
    #    self.parse_cfg()
    #    srcF = self.img.astype(np.float32)
    #    rect = search(src_img=self.img, **self.kargs)
    #    self.returnValSignal.emit(self.descriotion, rect)

    def run(self):
        """
        备用检测逻辑: 首先使用缩小图进行快速的Rect检测，只有当存在rect时，再使用原图大小进行检测
        :return:
        """
        srcF = self.img.astype(np.float32)
        #srcScaled = srcF[::4, ::4]
        srcScaled = cv2.resize(srcF, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_LINEAR)
        ## 缩小图快速排查rect
        rect = search(src_img=srcScaled, roi_size=0, board_size_range=[20, 50, 1], kernel_size=(50, 50),
                      outer_diameter_range=(5, 20),
                      ring_width_range=(1, 2), epsilon_dst=3, ring_threshold=[0.3, 0.8, 0.1])
        # 真正检查图像逻辑
        if rect.size != 0:
            rect = search(src_img=self.img, **self.kargs)
        #rect = search(src_img=self.img, **self.kargs)
        self.returnValSignal.emit(self.descriotion, rect)  # 向CoreSystem发送检测结果，在system.py-detect()中绑定
