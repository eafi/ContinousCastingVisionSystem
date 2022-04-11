"""
===========
Author: Yifei Zhang
Email: imeafi@gmail.com

对原有数据集进行增量更新
img_tar: 原有数据集图像目录 NOTE！ 请注意备份原有数据集
annotation_tar: 原有数据集标签目录 NOTE！ 请注意备份原有数据集
acc_img_root: 新增图像目录

本程序将遍历img_acc_root下所有图像，并对这些图像进行rect检查，将检查结果标签及其图像原图拷贝到img_tar和annotation_tar并保证不会覆盖原有数据集，
从而实现数据集扩充
"""

import sys
sys.path.append('../Detection_1')
from search import search
import os
import glob
import cv2
import argparse
import numpy as np


parse = argparse.ArgumentParser()
parse.add_argument('--origin_img_tar', type=str, default='F:/Dataset/MyData/CL')
parse.add_argument('--annotation_tar', type=str,default='E:/home/eafi/projects/py-projects/Labelling/Annotation')
parse.add_argument('--acc_img_root', type=str, default='F:/Dataset/samples')
args = parse.parse_args()

img_files = glob.glob(args.origin_img_tar+'/*.png')
annotation_files = glob.glob(args.annotation_tar+'/*.txt')
assert len(img_files) == len(annotation_files)
# 获取当前既有数据集的最大id值, 作为增量图像id的起始
acc_count = len(img_files)

acc_img_files = glob.glob(args.acc_img_root+'/*.png')

for img_file in acc_img_files:
    file_name = str(acc_count)
    txt_file_path = os.path.join(args.annotation_tar, file_name)
    txt_file = open(txt_file_path+'.txt', 'w')  # annotation
    src_img = cv2.imread(img_file, flags=cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(f'{args.origin_img_tar}/{acc_count}.png', src_img)
    src_img_f = src_img.astype(np.float32)
    bgr_src_img = cv2.cvtColor(src_img, cv2.COLOR_GRAY2RGB)
    rect = search(src_img=src_img_f, outer_diameter_range=(40, 100))
    if rect.size != 0:
        cv2.line(bgr_src_img, rect[0].astype(np.int32), rect[1].astype(np.int32), (0, 255, 255), 1)
        cv2.line(bgr_src_img, rect[1].astype(np.int32), rect[2].astype(np.int32), (0, 255, 255), 1)
        cv2.line(bgr_src_img, rect[2].astype(np.int32), rect[3].astype(np.int32), (0, 255, 255), 1)
        cv2.line(bgr_src_img, rect[3].astype(np.int32), rect[0].astype(np.int32), (0, 255, 255), 1)
        cv2.imshow('df', bgr_src_img)
        cv2.waitKey(0)
        txt_file.write('1')
        for i in rect:
            txt_file.write(f' {i[0]} {i[1]}')
        txt_file.write('\n')
    else:
        txt_file.write('0')
    txt_file.close()
    acc_count += 1



