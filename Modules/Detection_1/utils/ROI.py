"""
==========
Author: Yifei Zhang
Email: imeafi@gmail.com

接收ROI提取指令，返回指定区域ROI
input: img, roi_windows
output: roi_img
"""

import numpy as np
from LOG import *


def roi(src_img, roi_windows):
    """

    :param src_img:
    :param roi_windows: shape:(n, x1, y1, x2, y2)
    :return: list of roi windows.
    """
    assert roi_windows.ndim == 5, LOG(log_types.FAIL, "The shape of parameter: roi_windows is invalid.")
    roies = []
    for roi_window in roi_windows:
        x1, y1, x2, y2 = roi_window
        roi = src_img[y1:y2, x1:x2]
        roies.append(roi)
    return roies


if __name__ == "__main__":
    x = np.random.rand(3,3,3,3)
    roi(x, roi_windows=x)
    print(x.ndim)