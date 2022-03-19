"""
=========================
Author: Yifei Zhang
Email: imeafi@gmail.com

用于调试程序的虚拟相机，将指定文件夹的所有图像以视频流形式传送
"""

import glob

import numpy as np
from PIL import Image
import os
from itertools import chain

class Camera:
    def __init__(self, img_files=None):
        if img_files is None:
            root_path = '/home/eafi/Device/Dataset/FakeCamera'
            dirs = os.listdir(root_path)
            img_files = []
            for dir in dirs:
                path = os.path.join(root_path, dir, dir)
                img_files.append(glob.glob(path + '/*.png'))
            print(img_files)
            self.img_files = list(chain.from_iterable(img_files))
        else:
            self.img_files = img_files
        self.idx = 0


    def capture(self):
        if self.idx < len(self.img_files):
            img = np.asarray(Image.open(self.img_files[self.idx]))
            self.idx += 1
            return img
        else:
            return None




