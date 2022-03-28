from cv2 import Rodrigues
from numpy import zeros


def vecs2trans(rvec, tvec):
    """
    Rodrigues向量+平移向量转换成4x4变换矩阵
    :param rvec:
    :param tvec:
    :return:
    """
    trans = zeros((4, 4))
    rot, jac = Rodrigues(rvec)
    trans[:3, :3] = rot
    trans[:3, 3] = tvec.reshape(1, -1)
    trans[3, 3] = 1.0
    return trans
