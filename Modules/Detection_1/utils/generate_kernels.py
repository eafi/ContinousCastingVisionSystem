import numpy as np
import cv2



def generate_circular_mask(h, w, radius):
    """
    产生圆形mask
    :param h:
    :param w:
    :param radius:
    :return:
    """
    Y, X = np.ogrid[:h, :w]
    center = (int(w / 2), int(h / 2))
    dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)

    mask = dist_from_center <= radius
    return mask


def generate_ring_mask(inner_diameter, outer_diameter, size):
    """
    产生圆环mask
    :param size: 输出固定大小尺寸的kernel
    :return:
    """
    if not isinstance(inner_diameter, int) or not isinstance(outer_diameter, int):
        raise ValueError(f'the type of radius error. Expect: int but take: {inner_diameter}, {outer_diameter}')
    if inner_diameter > outer_diameter:
        inner_diameter, outer_diameter = outer_diameter, inner_diameter
    h = w = outer_diameter
    outer_mask = generate_circular_mask(h, w, outer_diameter // 2)
    inner_mask = generate_circular_mask(h, w, inner_diameter // 2)
    mask = outer_mask & (~inner_mask)

    # 固定尺寸：
    pattern = np.zeros(size, dtype=np.float32)
    pattern_h, pattern_w = size[0], size[1]
    pattern[(pattern_h-h)//2:(pattern_h-h)//2+h, (pattern_w-w)//2:(pattern_w-w)//2+w] = mask
    return pattern


def mask_to_kernel(mask):
    """
    将bool类型的mask转化成为cv识别的卷积核形似：
    1. 归一化
    2. CV_32F 浮点化
    :param mask:
    :return:
    """
    ones = mask.sum()
    kernel = mask.astype(np.float32) / ones
    return kernel

def generate_ring_kernels(outer_diameter_range, ring_width_range, kernel_size):
    """
    使用外经+内经不断便利卷积相应的ring kernel，找到卷积结果最大的那一个
    找到所有的圆环，并返回不断累计着色后的可能圆心位置图，这个可能的圆心位置需要进一步优化(search_4_points).
    :param outer_diameter_range: 外径范围
    :param ring_width_range: 环径范围
    :param src_img:
    :return:
    """
    if not isinstance(outer_diameter_range, tuple) and not isinstance(ring_width_range, tuple):
        raise ValueError('parameter is not tuple.')
    diameter_beg, diameter_end = outer_diameter_range
    ring_beg, ring_end = ring_width_range
    if diameter_end < 0 or diameter_end < 0 or ring_end < 0 or ring_beg < 0:
        raise ValueError('invalid scale.')
    if kernel_size[0] < outer_diameter_range[-1]:
        raise ValueError('[WARN] kernel size is smaller than ring.')
    # 循环内圈和外圈，找到最匹配的参数以及最大卷积结果位置
    acc_img = None
    kernels = []
    for ring in range(ring_beg, ring_end):
        for diameter in range(diameter_beg, diameter_end):
            inner_diameter = diameter - ring
            outer_diameter = diameter
            mask = generate_ring_mask(inner_diameter=inner_diameter, outer_diameter=outer_diameter, size=kernel_size)
            kernel = mask_to_kernel(mask)
            kernels.append(kernel)

    return kernels


def generate_rect_kernels(rect_size=[80,200,5], kernel_size=(200,200)):
    """
    使用方形kernel对图像进行conv，用于查找标定板估计的中心位置.
    :param rect_size: 估计标定板的可能尺寸
    :param kernel_size: 产生的滤波器将会被限制在这个范围，区域地方以0填充
    :return: 估计的标定板中心位置
    """
    kernels = []
    for i in range(*rect_size):
        mask = np.zeros(kernel_size)
        h, w = kernel_size
        mask[(h-i)//2:(h-i)//2+i, (w-i)//2:(w-i)//2+i] = np.ones((i,i))
        kernel = mask_to_kernel(mask)
        kernels.append(kernel)

    return kernels


def generate_board_kernels(ratio=2.0):
    """
    完全按照图纸尺寸，返回制定比例的board
    :param ratio 指定比例，注意在真实场景下，给board的分辨率只有200,对应物理尺寸的2倍，因此默认为2.0
    :return:
    """
    w = int(100 * ratio)
    h = int(100 * ratio)
    # 四个圆的圆心
    leftUpPos = (int(20 * ratio), int(35 * ratio))
    leftBotPos = (int(20 * ratio), int(75 * ratio))
    rightUpPos = (int(75 * ratio), int(35 * ratio))
    rightBotPos = (int(75 * ratio), int(75 * ratio))
    # 四个圆的半径
    leftUpRad   = 13.5 * ratio
    leftBotRad  = 8.5  * ratio
    rightUpRad  = 11   * ratio
    rightBotRad = 16   * ratio
    thickness = 3 * ratio

    kernels = []
    board = np.zeros(shape=(h, w), dtype=np.uint8)
    cv2.circle(board, center=leftBotPos, radius=int(leftBotRad), color=100, thickness=-1)
    cv2.circle(board, center=leftBotPos, radius=int(leftBotRad), color=255, thickness=int(thickness))
    cv2.circle(board, center=leftUpPos, radius=int(leftUpRad), color=100, thickness=-1)
    cv2.circle(board, center=leftUpPos, radius=int(leftUpRad), color=255, thickness=int(thickness))
    cv2.circle(board, center=rightBotPos, radius=int(rightBotRad), color=100, thickness=-1)
    cv2.circle(board, center=rightBotPos, radius=int(rightBotRad), color=255, thickness=int(thickness))
    cv2.circle(board, center=rightUpPos, radius=int(rightUpRad), color=100, thickness=-1)
    cv2.circle(board, center=rightUpPos, radius=int(rightUpRad), color=255, thickness=int(thickness))
    for i in range(4):
        wh = np.where(board==100)
        kernel = mask_to_kernel(board)
        kernel[wh] = -1.0
        kernels.append(kernel)
        board = cv2.rotate(board, cv2.ROTATE_90_CLOCKWISE)

    return kernels





