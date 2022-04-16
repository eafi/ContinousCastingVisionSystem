"""
===========
Author: Yifei Zhang
Email: imeafi@gmail.com

system.py是CoreSystem的执行主要backend文件，提供：
1. detection stage状态转移
2. detection方法资源调度和分配
3. detection结果处理以及解析成Target坐标
"""
import glob

from Modules.parse import *
from Modules.LOG import *
#from Modules.detect1 import Detection1
from Modules.Detection_1.utils.PnP import *
from PyQt5.QtCore import pyqtSignal, QThread, QTimer, QProcess
from multiprocessing import Process
from Modules.TargetObj import TargetObj
from Modules.utils import vecs2trans
from Modules.Robot import Robot
from CoreSystemGUI.CameraPanle.CoreSystemCameraWidget import CoreSystemCameraWidget
from time import sleep
from cv2 import Rodrigues
from scipy.spatial.transform import Rotation as R
from harvesters.core import Harvester
from platform import system
from Modules.detect1 import Detect


class initClass:
    cfgInit = False
    cameraInit = False
    torchInit = False
    robotInit = False


def test():
    while True:
        print('hhhh')


class CoreSystem(QThread):
    targetFoundSignal = pyqtSignal(str, np.ndarray)  # 主要用于CameraWidget的Target绘制工作，在CoreSystemMain.py绑定
    resourceInitOKSignal = pyqtSignal()  # 告知mainGUI资源初始化成功，在CoreSystemMain.py绑定:当资源分配成功后才能启动GUI
    newImgSignal = pyqtSignal()

    def __init__(self):
        super(CoreSystem, self).__init__()
        # CFG被其他控件更新后，需要发送相应信号，致使整个系统刷新Cfg
        # 如何发起cfg刷新？ 在Signal Map中查找并发送cfgUpdateSignal信号. 在LogWidget配置中有使用.
        self.coreSystemState = -1  # 系统检测宏观状态
        self.roiName = None
        self.DETECT_CFG_THREADS = 4  # 允许系统分配线程资源数
        self.targetObjs = {}  # 检测到的目标rect，用于检测target是否运动等信息，与TargetObj.py相关的操作
        self.tmpThread = None
        self.detect_enable = False
        self.detect_timers = QTimer()
        self.detect_timers.timeout.connect(self.detect_img_prompt)
        self.detect_timers.timeout.connect(self.detect_res_reader)
        self.detect_timers.start(1000)

    def run(self):
        """
        CoreSystem主执行循环，用于与Robot交互，并根据Robot请求进行状态转移.
        :return:
        """
        while True:
            if self.coreSystemState == -1:
                try:
                    # =================================#
                    # 关键资源分配，失败时将不断重新尝试初始化 #
                    # =================================#
                    self.core_resources_check()  # 资源分配
                    self.coreSystemState = 0  # 成功，进入静默状态
                    self.resourceInitOKSignal.emit()
                    LOG(log_types.OK, self.tr('System init good.'))
                except Exception as e:
                    LOG(log_types.FAIL, self.tr('CoreSystem initialization fail : ' + e.args[0]))
            elif self.coreSystemState == 0:  # 初始化成功状态，等待TCP请求
                sleep(2)
                self.coreSystemState = 1
                ## 相机状态与核心检测器的绑定: 每次相机状态刷新时，同时调用检测器
            #####################################################################################################
            #################################### PLC 请求相应函数 #################################################
            #####################################################################################################
            elif self.coreSystemState == 1:  # PLC命令启动检测,返回能源介质接头坐标
                self.detect_enable = True
                m = None
                self.roiName = 'LeftCameraTopROI'
                if 'LeftCameraTopROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraTopROI'].avg()
                if m is not None:
                    self.robot.set_system_mode(1)
                    self.robot.set_move_mat(m)
            elif self.coreSystemState == 2:  # PLC命令启动检测，返回水口安装坐标
                self.detect_enable = True
                m = None
                if 'LeftCameraLeftROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraLeftROI'].avg()
                elif 'LeftCameraRightROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraRightROI'].avg()
                if m is not None:
                    self.robot.set_system_mode(2)
                    self.robot.set_move_mat(m[0])
            elif self.coreSystemState == 3:  # 请求滑板液压缸坐标
                m = None
                if 'LeftCameraLeftROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraLeftROI'].avg()
                elif 'LeftCameraRightROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraRightROI'].avg()
                if m is not None:
                    self.robot.set_system_mode(3)
                    self.robot.set_move_mat(m[1])
            elif self.coreSystemState == 4:  # 请求水口坐标
                m = None
                if 'LeftCameraBottomROI' in self.targetObjs:
                    m = self.targetObjs['LeftCameraBottomROI'].avg()
                if m is not None:
                    self.robot.set_system_mode(4)
                    self.robot.set_move_mat(m)

    def core_resources_check(self):
        """各种组建资源初始化，当任何一个组件初始化失败，都将重新初始化
        :return:
        """
        # 读取CFG文件夹
        self.core_resource_cfg()
        # 分配相机资源
        self.core_resource_cameras()
        # CUDA状态
        self.core_resource_torch()
        # 机器人通讯资源
        self.core_resource_robot()
        self.d = Detect()
        self.p = Process(target=self.d.detect)
        self.p.start()


    def core_resource_cfg(self):
        if not initClass.cfgInit:
            self.cfgManager = CfgManager(path='CONF.cfg')
            self.cfg = self.cfgManager.cfg
            initClass.cfgInit = True
            self.DETECT_CFG_THREADS = self.cfgManager.DETECT_CFG_THREADS

    def core_resource_cameras(self):
        if not initClass.cameraInit:
            self.h = Harvester()
            if system() == 'Linux':
                self.h.add_file('/opt/mvIMPACT_Acquire/lib/x86_64/mvGenTLProducer.cti')
            else:
                self.h.add_file('C:/Program Files/MATRIX VISION/mvIMPACT Acquire/bin/x64/mvGenTLProducer.cti')
            self.h.update()
            LOG(log_types.NOTICE, self.tr('Camera List: '))
            print(self.h.device_info_list)
            self.camera_1 = self.h.create_image_acquirer(0)
            self.camera_2 = self.h.create_image_acquirer(1)
            self.camera_1.start()
            self.camera_2.start()
            initClass.cameraInit = True

    def core_resource_torch(self):
        if not initClass.torchInit:
            import torch
            self.cuda_available = torch.cuda.is_available()  # Status状态：cuda
            self.detectThread = []
            initClass.torchInit = True

    def core_resource_robot(self):
        if not initClass.robotInit:
            self.robot = Robot(cfg=self.cfg)
            self.robot.start()  # 不停发送系统状态
            self.robot.systemStateChange.connect(self.core_sys_state_change)
            initClass.robotInit = True

    def core_sys_state_change(self, state, datalst):
        self.coreSystemState = state


    def detect_res_reader(self):
        path = '.cache'
        files = glob.glob(path+'/*.npy')
        for file in files:
            print(file)
            split_name = os.path.splitext(os.path.basename(file))[0].split('-')
            roi_name = split_name[0]
            time_stamp = float(split_name[1])
            rect = np.load(file)
            os.remove(file)


            # PNP计算以及后处理
            rect = rect + np.array(self.cfg['ROIs_Conf'][roi_name][:2], dtype=np.float32)
            robot2Target = self.target_estimation(whichCamerawhichROI=roi_name, rect=rect)
            # 系统只返回静止状态下的标定, 因此系统将保存并分析检测到的任何标定板信息
            if roi_name not in self.targetObjs.keys():  # 全新找到的对象
                self.targetObjs[roi_name] = TargetObj(rect, robot2Target)
            else:
                # 之前已经该rect对象已经发现过，那么将新检测到的Rect坐标刷新进去
                self.targetObjs[roi_name].step(rect, robot2Target)

            self.targetFoundSignal.emit(roi_name, rect)  # 与CameraWidget有关，用于绘制Target




    def detect_img_prompt(self):
        """
        使用第一种方法进行核心图像检测.
        本方法一旦相机发送OK状态后就开始不断调用: 在main.py中已经与相机Status信号发送绑定.
        此外，应该先检查相机系统状态后，才能调用检测 -> state == 'OK'
        :return:
        """
        if self.detect_enable:
            img = self.camera_1.im_np  # 左相机图像
            roi = self.cfg['ROIs_Conf'][self.roiName]  # 提取当前系统阶段所需要的ROI区域
            roi_img = img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
            cv2.imwrite(f'.cache/{self.roiName}-{time.time()}.bmp', roi_img)


    def target_estimation(self, whichCamerawhichROI: str, rect: np.ndarray):
        """
        目标估计: 根据标定板的物理尺度进行PnP计算, 然后根据CFG刚体矩阵转换到目标抓取位置，最后根据手眼标定矩阵转换到机器人坐标系
        :param whichCamerawichROI:
        :param rect:
        :return:
        如果该ROI是左右两个标定板区域，那么需要计算两个Target: 水口安装位置 + 滑动液压钢位置 , 返回list
        如果该ROI是其他区域，那么只返回一个矩阵即可
        """
        # 哪一个ROI区域，用于决定哪一个刚体目标
        whichTarget = whichCamerawhichROI.split('Camera')[1].replace('ROI', 'Ref')

        # 获得目标板到刚体目标的转换矩阵(在parse。py中已经转化成矩阵)
        if whichTarget == 'LeftRef' or whichTarget == 'RightRef':
            # 左右参考标定板代表了两个坐标：水口安装位置 + 滑板液压缸安装位置，因此需要保存两个矩阵
            rect2Target = []
            rect2Target.append(self.cfg['RectRef2Target_Conf'][whichTarget + '1'])
            rect2Target.append(self.cfg['RectRef2Target_Conf'][whichTarget + '2'])
        else:
            rect2Target = self.cfg['RectRef2Target_Conf'][whichTarget]
        # 目标板已知绝对物理尺寸(在目标板左上角圆心为原点的坐标系下)
        rectPtsRef = get_four_points()
        # 得到目标板在相机坐标系下
        imgpts, rvec, tvec = pnp(rect, objp=rectPtsRef)
        camera2rect = vecs2trans(rvec=rvec, tvec=tvec)

        robot2Camera = self.cfg['HandEyeCalibration_Conf']['HandEyeMatrix']

        if isinstance(rect2Target, list):
            robot2Target = []
            robot2Target.append(robot2Camera @ camera2rect @ rect2Target[0])
            robot2Target.append(robot2Camera @ camera2rect @ rect2Target[1])
        else:
            robot2Target = robot2Camera @ camera2rect @ rect2Target

        return robot2Target
