"""
==========
Author: Yifei Zhang
Email: imeafi@gmail.com

"""

import cv2
import numpy as np

def draw(img, corners, imgpts):
    """
    绘制目标物体的物体坐标系原点轴系.
    :param img:
    :param corners: 相机尺度点集
    :param imgpts: 物理尺度轴系向相机尺度转化后的点集
    :return:
    """
    img = cv2.line(img, corners[0].astype(np.int32), tuple(imgpts[0].ravel().astype(np.int32)), (255,0,0), 5)
    img = cv2.line(img, corners[0].astype(np.int32), tuple(imgpts[1].ravel().astype(np.int32)), (0,255,0), 5)
    img = cv2.line(img, corners[0].astype(np.int32), tuple(imgpts[2].ravel().astype(np.int32)), (0,0,255), 5)
    return img


def get_four_points(width=55, height=50, vertical=True):
    """
    获取4points的理想坐标, 单位为毫米, x, y, z
    :param vertical: 竖直标定板，或横置标定板。默认为竖直
    :return:
    """
    objp = np.zeros((4, 3), np.float32)

    if vertical:
        objp[:, :2] = np.array(((0, 0), (height, 0), (height, width), (0, width)), dtype=np.float32)
    else:
        objp[:, :2] = np.array(((0, 0), (width, 0), (width, height), (0, height)), dtype=np.float32)
    return objp




def get_nozzle_points(side):
    """
    长水口操作点（或轴线）想对于左、右、中标定板的绝对物理尺度空间偏移.
    :param side:
    :return:
    """
    pos_map = {
        'left': np.float32([[50, -10, -100], [50, -60, -100]]),
        'right': np.float32([[-80, -10, -5], [-80, -60, -5]]),
        'middle': np.float32([[20, -100, -30], [20, -80, -30]])
    }
    # TODO: check if side is invalid.
    pos = pos_map[side]
    return pos


def draw_nozzle(img, corners, imgpts):
    """
    绘制长水口操作点（或轴线）
    :param img:
    :param corners: four points计算出来的点，相机坐标系下
    :param imgpts: 长水口操作点，已经完成从物体坐标系转化成相机坐标系
    :return:
    """
    # 链接原点与长水口轴线
    img = cv2.line(img, corners[0].astype(np.int32), tuple(imgpts[0].ravel().astype(np.int32)), (255,255,0), 5)
    return img




if __name__ == "__main__":
    get_four_points()



