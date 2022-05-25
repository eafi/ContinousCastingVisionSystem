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
# from Modules.detect1 import Detection1
from PyQt5.QtCore import pyqtSignal, QThread, QTimer, QProcess
from multiprocessing import Process
from Modules.BoardTracker import BoardTracker
from Modules.Robot import Robot
from Modules.Targets.Target_nozzle import Target_nozzle
from time import sleep
from harvesters.core import Harvester
from platform import system
from Modules.detect1 import Detect
import cv2


class initClass:
    cfgInit = False
    cameraInit = False
    torchInit = False
    robotInit = False


class CoreSystem(QThread):
    targetFoundSignal = pyqtSignal(str, np.ndarray)  # 主要用于CameraWidget的Target绘制工作，在CoreSystemMain.py绑定
    resourceInitOKSignal = pyqtSignal()  # 告知mainGUI资源初始化成功，在CoreSystemMain.py绑定:当资源分配成功后才能启动GUI

    def __init__(self):
        super(CoreSystem, self).__init__()
        # CFG被其他控件更新后，需要发送相应信号，致使整个系统刷新Cfg
        # 如何发起cfg刷新？ 在Signal Map中查找并发送cfgUpdateSignal信号. 在LogWidget配置中有使用.
        self.core_sys_state = -1  # 系统宏观状态，初始时-1，将初始化分配必要资源
        self.current_target = None
        self.roi_board_trackers = {}  # 以ROI name的字典，保存各个ROI的BoardTracker,返回稳定的board
        self.tmpThread = None
        self.detect_enable = False

        self.detect_timers = QTimer()
        self.detect_timers.timeout.connect(self.detect_img_prompt)
        self.detect_timers.timeout.connect(self.detect_res_reader)


    def run(self):
        """
        CoreSystem主执行循环，用于与Robot交互，并根据Robot请求进行状态转移.
        :return:
        """
        while True:
            if self.core_sys_state == -1:
                try:
                    # =================================#
                    # 关键资源分配，失败时将不断重新尝试初始化 #
                    # =================================#
                    self.core_resources_check()  # 资源分配
                    self.core_sys_state = 0  # 成功，进入静默状态
                    self.resourceInitOKSignal.emit()
                    LOG(log_types.OK, self.tr('System init good.'))
                except Exception as e:
                    LOG(log_types.FAIL, self.tr('CoreSystem initialization fail : ' + e.args[0]))
            elif self.core_sys_state == 0:  # 初始化成功状态，等待TCP请求
                self.core_sys_state = 2
                ## 相机状态与核心检测器的绑定: 每次相机状态刷新时，同时调用检测器
            #####################################################################################################
            #################################### PLC 请求相应函数 #################################################
            #####################################################################################################
            elif self.core_sys_state == 1:  # PLC命令启动检测,能源介质接头坐标
                self.detect_enable = True
                self.current_target = self.target_nozzle
            elif self.core_sys_state == 2:  # PLC命令启动检测，安装水口安装坐标
                self.detect_enable = True
                self.current_target = self.target_nozzle
            elif self.core_sys_state == 3:  # 请求安装滑板液压缸坐标
                self.detect_enable = True
                self.current_target = self.target_nozzle
            if self.current_target is not None:
                self.request_wait()

    def request_wait(self):
        """
        当PLC需求指定状态时，（使用roi_names指定检测哪一个（并非此函数功能）），
        本函数轮询检查TargetObj[roi_name]的计算情况，一旦计算完毕就会返回计算坐标,
        并向PLC发送指令
        :param target: 安装或卸载的目标，为Target.py的子类，定义了具体的Pnp计算
        :param roi_names:
        :param set_sys_mod:
        :param state: 安装或者卸载
        :return:
        """
        if self.current_target is None:
            return
        roi_names = self.current_target.roi_names
        if not isinstance(roi_names, list):
            roi_names = [roi_names]
        for roi_name in roi_names:
            if roi_name in self.roi_board_trackers:
                stable_rect = self.roi_board_trackers[roi_name].fetch_stable_rect() # 稳定后返回rect
                xyzrpy = self.current_target.target_estimation(mtx=self.cam_mtx,
                                         dist=self.cam_dist,
                                         cam2base=self.hand_eye,
                                         rect=stable_rect)
                if xyzrpy is not None:
                    self.robot.set_move_xyzrpy(xyzrpy)
                    self.robot.set_system_mode(self.core_sys_state)
                    self.core_sys_state = 0 # 系统回到静默状态

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
        # 目标物体初始化
        self.core_resource_targets()

        # =================  多进程检测 ================== #
        self.d = Detect(self.cache_path)
        self.p = Process(target=self.d.detect)
        self.p.start()
        self.detect_timers.start(500)

    def core_resource_cfg(self):
        if not initClass.cfgInit:
            self.cfgManager = CfgManager(path='CONF.cfg')
            self.cfg = self.cfgManager.cfg

            # 检测的缓冲图像文件夹
            self.cache_path = self.cfg['System_Conf']['CachePath']
            initClass.cfgInit = True

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
            # DEBUG

            #self.camera_1 = self.h.create_image_acquirer(serial_number='S1101390')
            #self.camera_2 = self.h.create_image_acquirer(serial_number='S1101391')
            self.left_cam = self.h.create_image_acquirer(0)
            self.right_cam = self.h.create_image_acquirer(1)
            self.left_cam.start()
            self.right_cam.start()

            self.left_cam_mtx = self.cfg['Calibration_Conf']['LeftCameraMatrix']
            self.left_cam_dist = self.cfg['Calibration_Conf']['LeftCameraDist']
            self.left_hand_eye = self.cfg['Calibration_Conf']['LeftHandEyeMatrix']

            self.right_cam_mtx = self.cfg['Calibration_Conf']['RightCameraMatrix']
            self.right_cam_dist = self.cfg['Calibration_Conf']['RightCameraDist']
            self.right_hand_eye = self.cfg['Calibration_Conf']['RightHandEyeMatrix']

            self.cam = self.left_cam
            self.cam_mtx = self.left_cam_mtx
            self.cam_dist = self.left_cam_dist
            self.hand_eye = self.left_hand_eye
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

    def core_resource_targets(self):
        """
        载入目标物体的相关信息
        :return:
        """
        self.target_nozzle = Target_nozzle(cfg=self.cfg)


    def core_sys_state_change(self, state, datalst):
        """
        在system.py文件中被与robot.systemStateChange绑定，用于获取最新的PLC请求状态
        :param state:
        :param datalst:
        :return:
        """
        #if self.core_sys_state != state:
        #    self.core_sys_state = state
        self.core_sys_state = 2

    def detect_res_reader(self):
        """
        对检测到的npy文件进行文件名(which camera which roi?)和检测内容解析，
        :return:
        """
        files = glob.glob(self.cache_path + '/*.npy')
        for file in files:
            print(file)
            split_name = os.path.splitext(os.path.basename(file))[0].split('-')
            roi_name = split_name[0]
            time_stamp = float(split_name[1])
            rect = np.load(file)
            os.remove(file)

            # !!从局部ROI返回到全局ROI坐标
            rect = rect + np.array(self.cfg['ROIs_Conf'][roi_name][:2], dtype=np.float32)
            # 将发现载入标定板绑定对象:
            if roi_name not in self.roi_board_trackers.keys():  # 全新找到的对象
                self.roi_board_trackers[roi_name] = BoardTracker(rect, roi_name)
            else:
                # 之前已经该rect对象已经发现过，那么将新检测到的Rect坐标刷新进去
                self.roi_board_trackers[roi_name].step(rect)

            self.targetFoundSignal.emit(roi_name, rect)  # 与CameraWidget有关，用于绘制Target

    def detect_img_prompt(self):
        """
        使用第一种方法进行核心图像检测.
        本方法一旦相机发送OK状态后就开始不断调用: 在main.py中已经与相机Status信号发送绑定.
        此外，应该先检查相机系统状态后，才能调用检测 -> state == 'OK'
        :return:
        """
        if self.detect_enable and self.current_target:
            img = self.cam.im_np
            for roi_name in self.current_target.roi_names:
                roi = self.cfg['ROIs_Conf']['LeftCamera'+roi_name]  # 提取当前系统阶段所需要的ROI区域
                roi_img = img[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]
                cv2.imwrite(f'../.cache/{roi_name}-{time.time()}.bmp', roi_img)
