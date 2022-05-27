"""
Author: Jia Han, Yifei Zhang
Email:              imeafi@gmail.com
"""
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


def camera_calibration(images, grid=(11,8), width=30):
    """
    张正友标定
    :param images: image files path
    :return:mtx: 相机内参矩阵
    dist: 畸变矩阵
    rvecs, tvecs 旋转外参和平移外参
    mask: 并非所有images都能检测到外参数，标记并排除找不到外参的图像
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
    mask = np.zeros(len(images),dtype=np.int32)
    for idx, fname in enumerate(images):
        img = cv2.imread(fname, cv2.IMREAD_GRAYSCALE)
        img = 255 - img
        bgr_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        ret, corners = cv2.findChessboardCorners(img, (h, w), None)
        print(fname)
        if ret == True:
            mask[idx] = 1
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(img, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            # Draw and display the corners
            cv2.drawChessboardCorners(bgr_img, (h, w), corners2, ret)
            #cv2.imshow('bgr', cv2.resize(bgr_img,None,fx=0.5,fy=0.5))
            print(fname, 'OK')
            #cv2.waitKey(33)
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, img.shape[::-1], None, None)
    print(rvecs, tvecs)
    print(mtx, dist)

    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    print("total error: {}".format(mean_error / len(objpoints)))
    tar2cam_r = []
    for rvec in rvecs:
        tar2cam_r.append(cv2.Rodrigues(rvec)[0])
    return mtx, dist, tar2cam_r, tvecs, mask

import glob
import os
def calibration():
    """
    1. 打开所有图像文件
    2. 相机标定, 返回外参数矩阵
    3. 手眼标定
    NOTE: 有两个相机，因此需要标定两次。
    :return:
    """
    ca_path = '../CalibrationImages' # 标定保存的图像和pos.txt文件夹
    #ca_path = 'E:/home/eafi/projects/py-projects/pythonProject5/res/111'
    sort_f = lambda x: int(os.path.splitext(os.path.basename(x))[0].split('-')[1])
    pos_files = glob.glob(f'{ca_path}/pos-*.txt')
    pos_files.sort(key=sort_f)
    for whichCamera in ['Left', 'Right']:
        img_files = glob.glob(f'{ca_path}/{whichCamera}-*.bmp')
        img_files.sort(key=sort_f) # 必须要按照编号顺序，因要与机械臂末端位置一一对应
        mtx, dist, tar2cam_r, tar2cam_t, mask = camera_calibration(images=img_files)
        h, w = cv2.imread(img_files[0], cv2.IMREAD_GRAYSCALE).shape
        #newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        np.save(f'../{whichCamera}_camera_matrix.npy', mtx)
        #np.save(f'{whichCamera}_camera_newmatrix.npy', newcameramtx)
        #np.save(f'{whichCamera}_camera_roi.npy', roi)
        np.save(f'../{whichCamera}_camera_dist.npy', dist)
        # ========== Hand Eye Calibration =============
        from scipy.spatial.transform import Rotation as R
        base2gri_r = []
        base2gri_t = []
        for pos_file, msk in zip(pos_files, mask):
            if msk == 0:
                continue
            f = open(pos_file, 'r')
            line = f.readline().split(',')[:-1]
            data = np.array([float(x) for x in line], dtype=np.float64)
            eluar = R.from_euler('ZYX', data[3:], degrees=True)

            matrix_r = eluar.as_matrix()
            trans = np.array(data[:3]).reshape(3, 1)
            trans = -matrix_r.transpose() @ trans

            base2gri_r.append(matrix_r.transpose())
            base2gri_t.append(trans)

        cam2base_r, cam2base_t = cv2.calibrateHandEye(R_target2cam=tar2cam_r, t_target2cam=tar2cam_t,
                                                      R_gripper2base=base2gri_r, t_gripper2base=base2gri_t,
                                                      method=cv2.CALIB_HAND_EYE_TSAI)
        m = np.zeros((4,4))
        m[:3, :3] = cam2base_r
        m[:3, 3] = cam2base_t.T
        m[3, 3] = 1.0
        np.save(f'../{whichCamera}_hand_eye_matrix.npy', m)
        print(whichCamera, cam2base_r, cam2base_t)

def rect_camera_calibration(file_path='F:/Dataset/FakeCamera'):
    """
    利用四圆环标定板进行相机标定
    :param file_path: 图像根目录,只接受bmp格式图片，并且以Conf文件ROI进行标定
    :return:
    """
    from Modules.parse import CfgManager
    import os
    from itertools import chain
    from Modules.Detection_1.search import search
    cfg = CfgManager('../CONF.cfg').cfg
    roi_name = 'LeftCameraLeftROI'
    roi = cfg['ROIs_Conf'][roi_name]

    img_files = glob.glob(path+'/*.bmp')

    # 理想标定板物理尺寸
    width = 55
    height = 50

    #  w = 50, h = 55 的标定板
    objp1 = np.zeros((4, 3), np.float32)
    objp1[:, :2] = np.array(((0, 0), (height, 0), (height, width), (0, width)), dtype=np.float32)

    # w = 55, h = 50的标定板
    objp2 = np.zeros((4, 3), np.float32)
    objp2[:, :2] = np.array(((0, 0), (width, 0), (width, height), (0, height)), dtype=np.float32)

    objpoints = []
    imgpoints = []
    for img_file in img_files[:20]:
        img = cv2.imread(img_file, cv2.IMREAD_GRAYSCALE)

        #roi_img = img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
        roi_img = img[2048-768:2048,2560-768:2560]
        cv2.imshow('roi', roi_img)
        cv2.waitKey(0)
        bgr_src = cv2.cvtColor(roi_img, cv2.COLOR_GRAY2BGR)
        rect = search(roi_img, roi_size=0)
        if rect.any():
            cv2.line(bgr_src, rect[0].astype(np.int32), rect[1].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[1].astype(np.int32), rect[2].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[2].astype(np.int32), rect[3].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[3].astype(np.int32), rect[0].astype(np.int32), (0, 255, 255), 1)
            cv2.imshow('found', bgr_src)
            # 判别标定板是横向还是竖向： 注意rect返回的 0-x, 1-y
            dw = rect[1][0] - rect[0][0] # 宽度
            dh = rect[-1][1] - rect[0][1] # 高度
            print(rect)
            if dw > dh : # 横向标定盘
                print('horizontal:',objp2)
                objpoints.append(objp2)
            else:
                print('vertical:', objp1)
                objpoints.append(objp1)

            imgpoints.append(rect[:,np.newaxis,:].astype(np.float32))
            cv2.waitKey(0)

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, (768,768), None, None, flags=cv2.CALIB_ZERO_TANGENT_DIST|cv2.CALIB_FIX_FOCAL_LENGTH)

    print(mtx, dist)
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    print("total error: {}".format(mean_error / len(objpoints)))


from scipy import io
if __name__ == '__main__':
    path = 'E:/home/eafi/projects/py-projects/pythonProject5/res/today_manual_2'
    #path = 'C:/Users/xjtu/Desktop/imgs/imgs/circiels'
    ###path = 'C:/Users/xjtu/Desktop/ca'

    calibration()

    #rect_camera_calibration(path)