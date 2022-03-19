"""
=========
Author: Yifei Zhang
Email: imeafi@gmail.com

对CONF.conf文件进行解码
"""
import os
from Modules.LOG import *
from PyQt5.QtCore import QObject, pyqtSignal
from Global_Val import Signal_Map

class CfgManager(QObject):
    cfgUpdateSignal = pyqtSignal()
    def __init__(self, path):
        super(CfgManager, self).__init__()
        self.path = path
        self.cfgUpdateSlot()  # 更新/初始化系统配置文件
        Signal_Map['CfgUpdateSignal'] = self.cfgUpdateSignal
        self.cfgUpdateSignal.connect(self.cfgUpdateSlot)

    def cfgUpdateSlot(self):
        """
        刷新CFG文件
        :return:
        """
        self.cfg = parse_cfg(self.path)
        parse_resources_cfg(self)
        parse_stage_rois(self)
        parse_target_ref(self)
        parse_roi_rect(self)  # 读取ROI rect信息


def parse_cfg(path: str):
    if not path.endswith(('.cfg') or not os.path.exists(path)):
        output = 'the cfg file not exist.'
        LOG(log_types.FAIL, output)
        raise FileNotFoundError(output)

    with open(path, 'r') as f:
        lines = f.read().split('\n')


    lines = [x.strip() for x in lines]
    lines = [x for x in lines if x and not x.startswith('#')]

    mdefs = {}
    conf_key = ''
    for line in lines:
        if line.startswith('['):
            conf_key = line[1:-1].strip()
            mdefs[conf_key] = {}
        else:
            key, val = line.split('=')
            key = key.strip()
            val = val.strip()
            mdefs[conf_key][key] = val

    return mdefs


def parse_resources_cfg(obj):
    """
    解析CFG文件的系统资源分配.
    注意！ 调用配置应该在cfg文件发生变更时，以及系统初始化时重新调用一次.
    :param obj: 包含了self.cfg的对象. 默认情况下应该是mainUI对象

    """
    assert 'Resources_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Resources Configuration.'))
    # 线程资源, 单相机最多检测线程数量。 每一张图像就开启了三个线程。
    cfg = obj.cfg['Resources_Conf']['ThreadResource']
    if 'mid' in cfg:
        obj.DETECT_CFG_THREADS = 8
    elif 'high' in cfg:
        obj.DETECT_CFG_THREADS = 16
    elif 'low' in cfg:
        obj.DETECT_CFG_THREADS = 4


def parse_stage_rois(obj):
    """
    解析CFG文件 : 不同阶段检测哪一个ROI的配置文件.
    1. 默认只使用LeftCamera， RightCamera只用作冗余；
    2. 第一阶段可以只用一个ROI，也可以使用两个ROI进行constrained限制性检测；
    3. 第二三阶段均只使用一个ROI
    4. 冗余相机、冗余ROI可以有意义的（服从视觉系统ROI编号映射关系条件下）替换，比如在第一阶段的两个ROI可以换成1和5,或者1和7等有意义的组合.
        具体替换需要在CFG文件中执行
    :param obj: 包含了self.cfg的对象，默认为mainUI对象
    :return:
    """
    assert 'DetectionStageROIs_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Stage Configuration.'))
    obj.cfg['DetectionStageROIs_Conf']['DetectionStage1'] =\
        obj.cfg['DetectionStageROIs_Conf']['DetectionStage1'].split(',')

    obj.cfg['DetectionStageROIs_Conf']['DetectionStage1Redundancy'] = \
        obj.cfg['DetectionStageROIs_Conf']['DetectionStage1Redundancy'].split(',')


def parse_target_ref(obj):
    """
    解析CFG文件： 每一个标定板在抓取目标坐标系下的物理偏移
    :param obj: 包含了self.obj的对象
    :return:
    """
    assert 'TargetRef2Rect_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Target Ref Configuration.'))
    for key in obj.cfg['TargetRef2Rect_Conf']:
        obj.cfg['TargetRef2Rect_Conf'][key] = [int(x) for x in obj.cfg['TargetRef2Rect_Conf'][key].split(',')]


def parse_roi_rect(obj):
    """
    对CFG文件的ROI rects进行解析.
    注意！ 两个相机的ROI是有区分的: 依据cameraType分为 LeftCamera and RightCamera.
    注意！ 本函数将会修改整个系统的cfg文件，将key=cameraType+ROIs_Conf的value从str转变为list of ints
    :return:
    """
    assert 'ROIs_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('ROIs configuration miss.'))
    ROIs_map = obj.cfg['ROIs_Conf']
    for key in ROIs_map:
        obj.cfg['ROIs_Conf'][key] = [int(x) for x in ROIs_map[key].split(',')]


def write_couple_cfg(couple: tuple, path='CONF.cfg'):
    """
    向path文件写入一对新的cfg键值对
    :param couple: 必须是一对, 且必须是str
    :param path:
    :return:
    """
    key, newVal = couple
    if not isinstance(key, str) or not isinstance(newVal, str):
        errorstr = 'Write to configuration value \'couple\' should be str tuple.'
        LOG(type=log_types.WARN, str=errorstr)
        raise TypeError(str)
    if key == '':
        return
    if not path.endswith(('.cfg') or not os.path.exists(path)):
        output = 'the cfg file not exist.'
        LOG(log_types.FAIL, output)
        raise FileNotFoundError(output)

    with open(path, 'r') as fr:
        with open('cfg.sw', 'w') as fw:
            for line in fr:
                keyLine = line.split('=')
                if key not in keyLine:
                    fw.write(line)
                else:
                    fw.write(key+'='+newVal+'\n')
        fr.close()
        fw.close()

    with open(path, 'w') as fw:
        with open('cfg.sw', 'r') as fr:
            data = fr.read()
            fw.write(data)
    fr.close()
    fw.close()
    os.remove('cfg.sw')



if __name__ == "__main__":
    #parse_cfg('CONF.cfg')

    pass
