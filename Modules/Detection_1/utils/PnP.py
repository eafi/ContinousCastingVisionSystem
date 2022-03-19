"""
==========
Author: Yifei Zhang
Email: imeafi@gmail.com

"""

import cv2
import numpy as np

cameraMatrx = np.array([
    1.2747839171870191e+03, 0., 7.5065264578273377e+02,
    0., 1.2747839171870191e+03, 4.8218924048281150e+02,
    0., 0., 1.], dtype=np.float32).reshape((3, 3))
cameraDist = np.array([
    -4.3548568186999093e-01,
    -2.1458383855925608e-01,
    -1.6018451329051601e-02,
    4.8998216858418845e-03,
    3.9005144897469193e+00], dtype=np.float32).reshape((1, 5))


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


def get_four_points(width=55, hight=50):
    """
    获取4points的理想坐标, 单位为毫米, x, y, z
    :return:
    """
    objp = np.zeros((4, 3), np.float32)
    objp[:, :2] = np.array(((0, 0), (width, 0), (width, hight), (0, hight)), dtype=np.float32)
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



def pnp(rect, mtx=cameraMatrx, dist=cameraDist, objp=None):
    """
    利用找到的四个点，以及理想的objp，结合相机参数计算出姿态信息
    :param objp:
    :param rect:
    :param mtx:
    :param dist: 畸变
    :return:
    """
    axis = np.float32([[50, 0, 0], [0, 50, 0], [0, 0, -50]]).reshape(-1, 3)
    if objp is None:
        objp = get_four_points()
    ret, rvecs, tvecs = cv2.solvePnP(objp, rect, mtx, dist)
    imgpts, jac = cv2.projectPoints(axis, rvecs, tvecs, mtx, dist)
    return imgpts, rvecs, tvecs



if __name__ == "__main__":
    get_four_points()



