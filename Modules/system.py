from Modules.parse import *
from Modules.LOG import *
from Modules.detect1 import Detection1
from Modules.Detection_1.utils.PnP import *
from PyQt5.QtCore import pyqtSignal
from Modules.TargetObj import TargetObj

class CoreSystem(QObject):
    targetFoundSignal = pyqtSignal(str, np.ndarray)  # 主要用于CameraWidget的Target绘制工作，在main.py绑定
    def __init__(self):
        super(CoreSystem, self).__init__()
        self.DETECT_STAGE = 1  # 系统检测宏观状态
        self.DETECT_CFG_THREADS = 4  # 允许系统分配线程资源数
        self.DETECT_STAGE1_CONSTRAINED = []  # Stage1 可能会使用两个ROIs检测窗进行综合检测
        self.DETECT_STAGE1_RECTS = []  # Stage1 多ROIs检测时，保存检测到的rects
        self.targetObjs = {}  # 检测到的目标rect，用于检测target是否运动等信息，与TargetObj.py相关的操作

        self.initCoreResources()

        # CFG被其他控件更新后，需要发送相应信号，致使整个系统刷新Cfg
        # 如何发起cfg刷新？ 在Signal Map中查找并发送cfgUpdateSignal信号. 在LogWidget配置中有使用.
        self.cfgManager = CfgManager()


    def initCoreResources(self):
        """各种组建资源初始化
        1. 左右相机资源初始化
        ??? 2. 检测线程初始化
        :return:
        """
        self.detectThread = []



    #def cfgUpdateSlot(self, path='CONF.cfg'):
    #    """
    #    刷新CFG文件
    #    :return:
    #    """
    #    self.cfg = parse_cfg(path)
    #    parse_resources_cfg(self)
    #    parse_stage_rois(self)
    #    parse_target_ref(self)
    #    parse_roi_rect(self)  # 读取ROI rect信息

    def threads_check(self, threads, maxNum):
        """
        动态更新可用线程资源
        :param threads: list of threads
        :param maxNum:
        :return:
        """
        newThreads = []
        for thread in threads:
            if thread.isRunning():
                newThreads.append(thread)
        threads = newThreads
        return True if len(newThreads) < maxNum else False


    def threads_return_slot(self, description: str, rect: np.ndarray):
        """
        处理线程返回结果:
        1. 发送找到Target信号，用于CameraWidget的Target绘制
        2. 针对不同系统Stage状态，按照Cfg文件进行目标Target几何位置关系的解析工作

        :param description: Detection线程返回描述str，用于描述处理的是哪一个相机的哪一快ROI. e.g. LeftCameraLeftROI
        :param rect: np.ndarray. 检测到的rect.
        :return:
        """
        if rect.size == 0:
            LOG(log_types.NOTICE, self.tr('In ' + description + ' Cannot found any rect.'))
        else:
            LOG(log_types.OK, self.tr('In ' + description + ' found rect!'))
            # 从ROI到相机全幅图像的坐标偏移
            rect = rect + np.array(self.cfg['ROIs_Conf'][description][:2], dtype=np.float32)
            if description not in self.targetObjs.keys():  # 全新找到的对象
                self.targetObjs[description] = TargetObj(rect)
            else:
                # 之前已经该rect对象已经发现过，那么将新检测到的Rect坐标刷新进去
                self.targetObjs[description].step(rect)

            # 根据系统状态解析Target最终的几何位置关系
            # 注意！这一步将Target坐标系转换到机械臂抓取的目标坐标系，因此CFG文件中Ref配置应该正确!!!
            self.target_estimation_switch_stage(whichCamerawhichROI=description, rect=rect)
        self.targetFoundSignal.emit(description, rect) # 与CameraWidget有关，用于绘制Target


    def detect(self, state: str):
        """
        使用第一种方法进行核心图像检测.
        本方法一旦相机发送OK状态后就开始不断调用: 在main.py中已经与相机Status信号发送绑定.
        此外，应该先检查相机系统状态后，才能调用检测 -> state == 'OK'
        :return:
        """
        sender = self.sender()  # one of CameraWidget
        # 确定系统所处阶段
        if state == 'OK':
            if self.threads_check(self.detectThread, self.DETECT_CFG_THREADS):
                roisMap = sender.get_roiImages()
                for key in roisMap:
                    tmpThread = Detection1(self.cfgManager.cfg, description=key, img=roisMap[key])
                    tmpThread.returnValSignal.connect(self.threads_return_slot)
                    self.detectThread.append(tmpThread)
                    tmpThread.start()


    def target_estimation_switch_stage(self, whichCamerawhichROI: str, rect: np.ndarray):
        """
        依据：
        1. 视觉系统当前状态Stage
        2. 配置文件DetectionStageROIs_Conf需要哪个相机的哪个ROI
        对具体的target_estimation方法进行选择. 由于第一状态可能存在Constrained情况，稍微复杂一点。
        :param whichCamerawhichROI:
        :param rect:
        :return:
        """
        assert self.DETECT_STAGE == 1 or \
               self.DETECT_STAGE == 2 or \
               self.DETECT_STAGE == 3, LOG(log_types.FAIL, self.tr(f'Vision system in invalid stage: {self.DETECT_STAGE}'))

        if self.DETECT_STAGE == 1:
            stage1conf = self.cfg['DetectionStageROIs_Conf']['DetectionStage1']
            if len(stage1conf) == 1:
                if whichCamerawhichROI in stage1conf:  # 单ROI估计
                    self.target_estimation_single(whichCamerawhichROI, rect)
            elif whichCamerawhichROI in stage1conf \
                    and whichCamerawhichROI not in self.DETECT_STAGE1_CONSTRAINED:  # 多ROI且之前没看到过
                self.DETECT_STAGE1_CONSTRAINED.append(whichCamerawhichROI)
                self.DETECT_STAGE1_RECTS.append(rect)
                if len(stage1conf) == len(self.DETECT_STAGE1_CONSTRAINED):
                    self.target_estimation_multi(self.DETECT_STAGE1_CONSTRAINED, rects=self.DETECT_STAGE1_RECTS)
                    self.DETECT_STAGE1_RECTS = []
                    self.DETECT_STAGE1_CONSTRAINED = []
        elif self.DETECT_STAGE == 2 or self.DETECT_STAGE == 3:
            stageconf = self.cfg['DetectionStageROIs_Conf'][f'DetectionStage{self.DETECT_STAGE}']
            if whichCamerawhichROI in stageconf:
                self.target_estimation_single(whichCamerawichROI=whichCamerawhichROI, rect=rect)


    def target_estimation_multi(self, whichCamerawhichROIs: list, rects: list):
        """
        视觉系统状态, 根据是否是多ROI进行目标的PnP计算.
        :param whichCamerawhichROIs:
        :param rects:
        :return:
        """
        tvecs = []
        for whichCamerawhichROI, rect in zip(whichCamerawhichROIs, rects):
            imgpts, rvec, tvec = self.target_estimation_single(whichCamerawhichROI, rect)
            tvecs.append(tvec)
        print(np.mean(tvecs, axis=1))




    def target_estimation_single(self, whichCamerawichROI: str, rect: np.ndarray):
        """
        视觉系统状态2, 单ROI进行PnP计算
        :param whichCamerawichROI:
        :param rect:
        :return:
        """
        targetRef = np.array(self.cfg['TargetRef2Rect_Conf'][whichCamerawichROI.replace('ROI', 'Ref')], dtype=np.float32).reshape((3,1))
        rectPtsRef = get_four_points()
        imgpts, rvec, tvec = pnp(rect, objp=rectPtsRef)
        tvec = tvec - targetRef
        print(tvec)
        return imgpts, rvec, tvec
