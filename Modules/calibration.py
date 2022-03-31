import cv2
import numpy as np

def skew(v):
    import numpy as np
    return np.array([[0, -v[2], v[1]],
                     [v[2], 0, -v[0]],
                     [-v[1], v[0], 0]])


def hand_eye_calibration(A, C, flag=1):
    #  ------手眼标定函数, 两种情况，0、眼在手上；1、眼在手外
    #  机械臂末端到基坐标系的位姿转换矩阵     A ---- (4 * n, 4)
    #  相机到标定板的位姿变换矩阵,相机外参    C ---- (4 * n, 4)
    # 导入库

    # 读取输入参数的个数
    num = A.shape[0] / 4
    num = int(num)
    # ---------------------------------------------
    # 计算部分
    # 1、生成数据，每两组数据可以得到一组 AX=XB 形式的数据
    #    一共生成num-1组数据
    Hgij = np.zeros((num * 4 - 4, 4))
    Hcij = np.zeros((num * 4 - 4, 4))
    # 矩阵相乘，用np.dot()
    # 判定是哪种情况，flag=0，则为眼在手上, 即相机在机械臂上
    # ------------，flag=1，则为眼在手外，即想在安装在外部，不会移动
    if (flag == 1):
        for i in range(num - 1):
            Hgij[4 * i:4 * i + 4, :] = np.dot(A[4 * (i + 1):4 * (i + 1) + 4, :], np.linalg.inv(A[4 * i:4 * i + 4, :]))
            Hcij[4 * i:4 * i + 4, :] = np.dot(C[4 * (i + 1):4 * (i + 1) + 4, :], np.linalg.inv(C[4 * i:4 * i + 4, :]))
    else:
        for i in range(num - 1):
            Hgij[4 * i:4 * i + 4, :] = np.dot(np.linalg.inv(A[4 * i:4 * i + 4, :]), A[4 * (i + 1):4 * (i + 1) + 4, :])
            Hcij[4 * i:4 * i + 4, :] = np.dot(np.linalg.inv(C[4 * i:4 * i + 4, :]), C[4 * (i + 1):4 * (i + 1) + 4, :])

    # 提取旋转矩阵 与 平移矩阵
    Rgij = np.zeros((num * 3 - 3, 3))
    Tgij = np.zeros((num * 3 - 3, 1))
    Rcij = np.zeros((num * 3 - 3, 3))
    Tcij = np.zeros((num * 3 - 3, 1))

    for i in range(num - 1):
        Rgij[3 * i:3 * i + 3, :] = Hgij[4 * i:4 * i + 3, 0:3]
        Tgij[3 * i:3 * i + 3, :] = Hgij[4 * i:4 * i + 3, 3:4]
        Rcij[3 * i:3 * i + 3, :] = Hcij[4 * i:4 * i + 3, 0:3]
        Tcij[3 * i:3 * i + 3, :] = Hcij[4 * i:4 * i + 3, 3:4]

    pinA = np.zeros((num * 3 - 3, 3))
    b = np.zeros((num * 3 - 3, 1))
    # 开始计算
    for i in range(num - 1):
        # Step1:利用罗德里格斯变换将旋转矩阵转换为旋转向量
        rgij = cv2.Rodrigues(Rgij[3 * i:3 * i + 3, :])[0]
        rcij = cv2.Rodrigues(Rcij[3 * i:3 * i + 3, :])[0]
        # Step2:向量归一化
        theta_gij = np.linalg.norm(rgij)
        rngij = rgij / theta_gij
        theta_cij = np.linalg.norm(rcij)
        rncij = rcij / theta_cij
        # Step3:修正的罗德里格斯参数表示姿态变化
        Pgij = 2 * np.sin(theta_gij / 2) * rngij
        Pcij = 2 * np.sin(theta_cij / 2) * rncij
        # Step4:计算初始旋转向量P’cg, 其中skew一定是奇异的，至少需要两组数据才能求解
        pinA[3 * i: 3 * i + 3, :] = skew(np.squeeze(Pgij + Pcij))
        b[3 * i:3 * i + 3, :] = Pcij - Pgij
    # Step4:计算初始旋转向量P’cg, 其中skew一定是奇异的，至少需要两组数据才能求解
    Pcg_prime = np.dot(np.dot(np.linalg.inv(np.dot(pinA.T, pinA)), pinA.T), b)
    # Step5:计算旋转向量Pcg
    Pcg = 2 * Pcg_prime / np.sqrt(1 + (np.linalg.norm(Pcg_prime)) * (np.linalg.norm(Pcg_prime)))
    # Step6:计算旋转矩阵Rcg
    Rcg1 = np.dot((1 - ((np.linalg.norm(Pcg) * (np.linalg.norm(Pcg))) / 2)), np.eye(3))
    Rcg2 = 0.5 * (np.dot(Pcg, Pcg.T) + np.sqrt(4 - np.linalg.norm(Pcg) * np.linalg.norm(Pcg)) * skew(np.squeeze(Pcg)))
    Rcg = Rcg1 + Rcg2
    print(Rcg)
    # Step7:计算平移向量Tcg
    T_cg1 = np.zeros((num * 3 - 3, 1))
    T_cg2 = np.zeros((num * 3 - 3, 3))
    for i in range(num-1):
        T_cg1[3 * i:3 * i + 3, :] = np.dot(Rcg, Tcij[3 * i:3 * i + 3, :]) - Tgij[3 * i:3 * i + 3, :]
        T_cg2[3 * i:3 * i + 3, :] = Rgij[3 * i:3 * i + 3, :] - np.eye(3)
    Tcg = np.dot(np.dot(np.linalg.inv(np.dot(T_cg2.T, T_cg2)), T_cg2.T), T_cg1)

    T_cam = np.zeros((4, 4))
    T_cam[0:3, 0:3] = Rcg
    T_cam[0:3, 3:4] = Tcg
    T_cam[3, 3] = 1
    print(T_cam)
    return T_cam


## 测试函数
#def main():
#    from scipy import io
#    # 读取matlab里面的.mat文件， 很可能是直接把当时所有的变量都进行了保存
#    mat = io.loadmat('A.mat')
#    # 找到需要从参数，读取并转换为numpy格式
#    A = np.array(mat['A'], np.float32)
#    C = np.array(mat['C'], np.float32)
#    # 打印读取到的变量的基本信息
#    # print(A.dtype)
#    # print(A.shape)
#    # print(type(A))
#    # print(A.shape[0] / 4)
#    hand_eye_cla(A, C, 0)


def camera_calibration(images, grid=(11, 8), width=35):
    """
    张正友标定
    :return:
    """
    h, w = grid
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((h * w, 3), np.float32)
    objp[:, :2] = width * np.mgrid[0:h, 0:w].T.reshape(-1, 2)
    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.
    img = None
    for fname in images:
        img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
        img = 255 - img
        ret, corners = cv2.findChessboardCorners(img, (w, h), None)
        if ret == True:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(img, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners)
            # Draw and display the corners
            cv2.drawChessboardCorners(img, (h, w), corners2, ret)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img.shape[::-1], None, None)
    # print(rvecs, tvecs)
    print(mtx)

    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    print("total error: {}".format(mean_error / len(objpoints)))
    return mtx, dist, rvecs, tvecs

import glob
from Modules.utils import vecs2trans
def calibration(robotPos, grid=(11, 8), width=35):
    """
    :param robotMovePos: 机械臂移动末端位置
    :param grid: 棋盘格数量
    :param width: 棋盘格宽度(mm)
    1. 打开所有图像文件
    2. 相机标定, 返回外参数矩阵
    3. 手眼标定
    NOTE: 有两个相机，因此需要标定两次。
    :return:
    """
    for whichCamera in ['Left', 'Right']:
        images = glob.glob(f'../CalibrationImages/{whichCamera}-*.png')
        images = sorted(images)  # 必须要按照编号顺序，因为要与机械臂末端位置一一对应
        mtx, dist, rvecs, tvecs = camera_calibration(images=images)
        # 将一一计算出来的外参数转换成手眼标定能够识别的矩阵
        rvecs = np.array(rvecs).squeeze()
        tvecs = np.array(tvecs).squeeze()
        C = []
        for rvec, tvec in zip(rvecs, tvecs):
            trans = vecs2trans(rvec=rvec, tvec=tvec) # 向量转矩阵
            C.append(trans)
        C = np.array(C).reshape(-1, 4)
        A = []
        for pts in robotPos:
            tvec = np.array(pts[:3])
            rvec = np.array(pts[3:])
            trans = vecs2trans(rvec=rvec, tvec=tvec)
            A.append(trans)
        A = np.array(A).reshape(-1, 4)
        # 手眼标定
        hand_eye_calibration(A, C)
