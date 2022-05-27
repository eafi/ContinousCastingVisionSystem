"""
=========
Author: Yifei Zhang
Email: imeafi@gmail.com

对CONF.conf文件进行解码
"""
import functools
import os

import numpy as np

from Modules.LOG import *
from PyQt5.QtCore import QObject, pyqtSignal
from Global_Val import Signal_Map

from platform import system
if system() == 'Linux':
    open = open
else:
    open = functools.partial(open, encoding='utf-8')

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
        parse_target_ref(self)
        parse_roi_rect(self)  # 读取ROI rect信息
        parse_network(self)
        parse_robot_camera_matrix(self) # 解析标定结果矩阵
        parse_target_circle(self) # 解析每个目标的拟合圆


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


def parse_target_ref(obj):
    """
    解析CFG文件： 每一个标定板与目标刚体的转换矩阵
    :param obj: 包含了self.obj的对象
    :return:
    """
    assert 'Tar2Board_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Target Ref Configuration.'))
    from scipy.spatial.transform import Rotation as R
    for key in obj.cfg['Tar2Board_Conf']:
        obj.cfg['Tar2Board_Conf'][key] = [float(x) for x in obj.cfg['Tar2Board_Conf'][key].split(',')]
        eular = R.from_euler('ZYX', [obj.cfg['Tar2Board_Conf'][key][-3:]])
        trans = np.array(obj.cfg['Tar2Board_Conf'][key][:3])
        m = np.zeros((4,4))
        m[:3,:3] = eular.as_matrix()
        m[:3, 3] = trans
        m[3,3] = 1.0
        obj.cfg['Tar2Board_Conf'][key] = m

def parse_robot_camera_matrix(obj):
    """
    确定各个标定文件是否存在, 并读取该文件
    :param obj:
    :return:
    """
    assert 'Calibration_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Calibration Configuration.'))
    for key in obj.cfg['Calibration_Conf']:
        val = obj.cfg['Calibration_Conf'][key]
        assert os.path.exists(val)
        obj.cfg['Calibration_Conf'][key] = np.load(val)

def parse_target_circle(obj):
    assert 'TargetCircle_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Cannot find Target Cicle Configuration.'))
    for key in obj.cfg['TargetCircle_Conf']:
        val = [float(x) for x in obj.cfg['TargetCircle_Conf'][key].split(',')]
        obj.cfg['TargetCircle_Conf'][key] = val



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
        obj.cfg['ROIs_Conf'][key] = [int(float(x)) for x in ROIs_map[key].split(',')]


def parse_network(obj):
    """
    解析CFG文件： 对Network配置进行解析
    :param obj:
    :return:
    """
    assert 'Network_Conf' in obj.cfg, LOG(log_types.FAIL, obj.tr('Network configuration miss.'))
    Network_map = obj.cfg['Network_Conf']

    for key in Network_map:
        if key == 'PORT':
            obj.cfg['Network_Conf'][key] = int(obj.cfg['Network_Conf']['PORT'])
        elif key != 'IP':
            # 对其余Network指令进行uint32解码
            obj.cfg['Network_Conf'][key] = int(obj.cfg['Network_Conf'][key], 16)




def write_couple_cfg(couple: tuple, path='CONF.cfg'):
    """
    向path文件写入一对新的cfg键值对
    :param couple: 必须是一对, 且必须是str (Key_Name_str, Value_str)
    :param path:
    :return:
    """
    dir = path.split('CONF.cfg')[0]
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
        with open(dir+'cfg.sw', 'w', encoding='utf-8') as fw:
            for line in fr:
                keyLine = line.split('=')
                if key not in keyLine:
                    fw.write(line)
                else:
                    fw.write(key+'='+newVal+'\n')
        fr.close()
        fw.close()

    with open(path, 'w') as fw:
        with open(dir+'cfg.sw', 'r') as fr:
            data = fr.read()
            fw.write(data)
    fr.close()
    fw.close()
    os.remove(dir+'cfg.sw')



if __name__ == "__main__":
    manager = CfgManager('../CONF.cfg')

    pass
