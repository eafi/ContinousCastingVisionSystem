from cv2 import Rodrigues
import numpy as np
from scipy.spatial.transform import Rotation as R

def cv2trans(rvec, tvec):
    """
    Rodrigues向量+平移向量转换成4x4变换矩阵
    :param rvec:
    :param tvec:
    :return:
    """
    trans = np.zeros((4, 4))
    rot, jac = Rodrigues(rvec)
    trans[:3, :3] = rot
    trans[:3, 3] = tvec.T
    trans[3, 3] = 1.0
    return trans


def trans2xyzrpy(trans):
    eular = R.from_matrix(trans[:3, :3]).as_euler('ZYX', degrees=True)
    trans = trans[:3, 3]
    data = 6 * [np.float32(0.0)]
    data[:3] = trans
    data[3:] = eular
    return data


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
