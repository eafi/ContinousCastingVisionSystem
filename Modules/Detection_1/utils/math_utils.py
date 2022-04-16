import numpy as np
import torch
from torch.nn.functional import conv2d

eps = np.finfo(np.float32).eps.item()
def slope_dist(pt1, pt2):
    return (pt1[1] - pt2[1]) / (pt1[0] - pt2[0] + eps), np.linalg.norm(pt1-pt2, ord=2)


def cos_sim(pt1, pt2, pt3, pt4):
    p12 = pt2 - pt1
    p34 = pt4 - pt3
    c = np.dot(p12, p34) / (np.linalg.norm(p12)*np.linalg.norm(p34))
    return c

"""
GPU part:
"""
import time
@torch.no_grad()
def conv(img, kernels):
    """

    :param img: numpy array. (batch, 1, h, w) cvt to Tensor (batch,1,  h, w)
    :param kernels: numpy array. (num kernels, h, w)cvt to Tensor
    :return: 分组卷积，有多少层kernels就输出多少曾结果
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    if len(img.shape) == 2: # single channel and batch
        tensor_img = torch.tensor(img).unsqueeze(0).unsqueeze(0).float().to(device)
    elif len(img.shape) == 3: # multi channel and single batch
        tensor_img = torch.tensor(img).unsqueeze(0).permute(0, 3, 1, 2).float().to(device)
    else: # four dims 既然已是四通道，默认用户知道torch组织形式
        tensor_img = torch.tensor(img).float().to(device)
    with torch.no_grad():
        tensor_ker = torch.tensor(kernels, requires_grad=False).unsqueeze(1).float().to(device)
        output = conv2d(tensor_img, tensor_ker, stride=1, bias=None, groups=1, padding=0).squeeze()
        output = output.to('cpu').numpy()
    return output






def weighted_mean_pos(img):
    """
    输入一张图片，输出这个图片的权重中心点，越亮的位置越有可能成为中心.
    :param img:
    :return:
    """
    h, w = img.shape
    x = np.arange(0, w)
    y = np.arange(0, h)
    xv, yv = np.meshgrid(x, y)
    mean_x = np.sum(xv * img[yv, xv]) / np.sum(img)
    mean_y = np.sum(yv * img[yv, xv]) / np.sum(img)
    print(mean_x,',', mean_y)
    return np.array((mean_y, mean_x))
