from PyQt5.QtWidgets import QFrame
import time
class log_colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class log_types:
    WARN = log_colors.WARNING+'[WARN]'+log_colors.ENDC
    FAIL = log_colors.FAIL+'[FAIL]'+log_colors.ENDC
    NOTICE = log_colors.FAIL+'[NOTICE]'+log_colors.ENDC
    OK = log_colors.OKCYAN+'[OK]'+log_colors.ENDC


def LOG(type, str, core=None):
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    # 获取系统信息
    core_str = ""
    if core is not None:
        core_str = log_colors.BOLD+core.get_info()+log_colors.ENDC
    print(time_str+' '+type+' '+core_str+' '+str)

