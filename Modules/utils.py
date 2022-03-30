from cv2 import Rodrigues
import numpy as np
from scipy.spatial.transform import Rotation as R

def vecs2trans(rvec, tvec):
    """
    Rodrigues向量+平移向量转换成4x4变换矩阵
    :param rvec:
    :param tvec:
    :return:
    """
    trans = np.zeros((4, 4))
    rot, jac = Rodrigues(rvec)
    trans[:3, :3] = rot
    trans[:3, 3] = tvec.reshape(1, -1)
    trans[3, 3] = 1.0
    return trans


def trans2vecs(trans):
    eular = R.from_matrix(trans[:3, :3]).as_euler('xyz', degrees=True)  # 外旋角度制
    trans = trans[:3, 3]
    data = 6 * [np.float32(0.0)]
    data[:3] = trans
    data[4:] = eular
    return data
