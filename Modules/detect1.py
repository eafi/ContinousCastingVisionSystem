"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

detect1.py文件提供了Detection_1方法的Qt封装，以Qthread的形式向CoreSystem提供核心检测方法支持
"""
import glob
import os

from PyQt5.QtCore import QThread, pyqtSignal
from Modules.LOG import *
from Modules.Detection_1.search import search
from Modules.Detection_1.utils.PnP import *
import numpy as np
import cv2
from collections import deque


class Detect:
    def __init__(self):
        super(Detect, self).__init__()


    def detect(self):
        path = '../.cache'
        while True:
            files = glob.glob(path+'/*.bmp')
            for file in files:
                print('file found!')
                img = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
                # srcScaled = srcF[::4, ::4]
                # srcScaled = cv2.resize(srcF, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_LINEAR)
                ### 缩小图快速排查rect
                # rect = search(src_img=srcScaled, roi_size=0, board_size_range=[20, 50, 1], kernel_size=(50, 50),
                #              outer_diameter_range=(5, 20),
                #              ring_width_range=(1, 2), epsilon_dst=3, ring_threshold=[0.3, 0.8, 0.1])
                ## 真正检查图像逻辑
                # if rect.size != 0:
                #    rect = search(src_img=self.img, **self.kargs)
                start_time = time.time()
                rect = search(src_img=img)
                print(f'!!!!!!!!!!!!!!!!!!!!!!!!!!!!! time: {time.time() - start_time}')
                os.remove(file)
                if rect.size != 0:
                    split_name = os.path.splitext(os.path.basename(file))[0]
                    save_path = os.path.join(path, split_name)+'.npy'
                    np.save(save_path, rect)
                # self.returnValSignal.emit(rect)  # 向CoreSystem发送检测结果，在system.py-detect()中绑定

