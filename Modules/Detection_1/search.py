"""
=======
Author: Yifei Zhang
Email: imeafi@gmail.com

实现对输入图像进行标定板查找，并返回所寻找到的四个圆心位置。以(left-top, right-top, right-bottom, left-bottom)顺序输出像素坐标.
主函数为 search()
"""
import glob
import sys
import time

import cv2
import numpy as np

sys.path.append('/home/eafi/projects/py-projects/Qt1')
from itertools import combinations
from Modules.Detection_1.utils.math_utils import *
from Modules.Detection_1.utils.generate_kernels import *
from Modules.LOG import *
import argparse

def search_ROI_center(output):
    """
    从卷积结果中找较大的区域，平均这些区域的中心位置作为ROI中心点
    :param output: (batch, h, w) 从卷及结果中找到平均中心位置，作为ROI的中心点
    :return:
    """
    # find ROI
    mean_poses = []
    #img = np.zeros_like(output[0], dtype=np.uint8)
    for i in range(output.shape[0]):

        # (y, x)
        threshold_img = output[i] > 0.3
        pos = np.where(threshold_img==True)
        if len(pos[0]) == 0:
            break

        mean_pos = np.mean(pos, axis=1)
        mean_poses.append(mean_pos)  # (y, x)
        #cv2.circle(img, mean_pos[::-1].astype(np.uint8), 2, 255, -1)
        #cv2.imshow('track', img)
        #cv2.waitKey(0)


    # center_pos : (y, x)
    if mean_poses:
        center_pos = np.mean(mean_poses, axis=0).astype(np.int32) # ROI必须要是整数，否则访问无效
    else:
        center_pos = np.array((0, 0), dtype=np.float32)
    return center_pos


def search_4_points(acc_img, area_threshold, pts_type='avg'):
    """
    1. 联通器删除掉acc中最大的面积
    2. 剩下的小面积提取出重心坐标
    :param acc_img: 累计圆环可能的圆心位置,包含了噪声和不良区域，需要使用联通器进行过滤
    :param area_threshold: 使用area来约束不利区域，但是可能还是包含噪声区域
    :param pts_type: 点的统计方法，'centroids' or 'avg'
    :return:
    """

    #bgr_acc_img = cv2.cvtColor(acc_img, cv2.COLOR_GRAY2BGR)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(acc_img, connectivity=8)
    #print('total labels: ', num_labels)
    valid_centroids = []
    for label in range(1, num_labels):
        # DEBUG
        #print('label:', label)
        # DEBUG
        # 筛选有效spot
        if area_threshold[0] <= stats[label][cv2.CC_STAT_AREA] < area_threshold[1]:
            #bgr_acc_img = cv2.circle(bgr_acc_img, centroids[label].astype(np.int32), radius=2, color=(0, 0, 255),thickness=-1)
            if pts_type == 'avg':
                avg_pts = np.mean(np.where(labels == label), axis=1)[::-1] # y,x -> x,y 服从全局
                #print('average pos: ', avg_pts)
                valid_centroids.append(avg_pts)
            else:
                #print('centrods pos:', centroids[label])
                valid_centroids.append(centroids[label])

    # DEBUG
    #cv2.imshow('bgr_acc_img', bgr_acc_img)
    # DEBUG
    #print('[INFO] valid centroids: ', valid_centroids)
    return valid_centroids



def search_rect(points, img, epsilon_k=0.01, epsilon_dst=15):
    """
    将提取出来的一系列点进行矩形匹配
    :param points: x,y
    :return: X, y
    """
    if len(points) < 4:
        #print('[WARNING] no more than 4 points detected.')
        #LOG(log_types.NOTICE, 'no more than 4 points detected.')
        pass

    for pts in combinations(points, 4):
        #bgr_acc_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        #print('combination for 4: ',pts)
        # 以x进行排序
        pts = sorted(pts, key=lambda x:x[0])
        #print('sorted via x: ', pts)
        left_2_pts, right_2_pts = pts[:2], pts[2:]
        # 以y进行排序
        left_2_pts = sorted(left_2_pts, key=lambda x: x[1])
        right_2_pts = sorted(right_2_pts, key=lambda x: x[1])
        lt_pts = np.array(left_2_pts[0])
        lb_pts = np.array(left_2_pts[1])
        rt_pts = np.array(right_2_pts[0])
        rb_pts = np.array(right_2_pts[1])
        #print('left top: ', lt_pts)
        #print('left bot: ', lb_pts)
        #print('right top: ', rt_pts)
        #print('right bot: ', rb_pts)
        #cv2.circle(bgr_acc_img, lt_pts.astype(np.int32), 2, (0,0,255), thickness=-1)
        #cv2.circle(bgr_acc_img, lb_pts.astype(np.int32), 2, (0,0,255), thickness=-1)
        #cv2.circle(bgr_acc_img, rt_pts.astype(np.int32), 2, (0,0,255), thickness=-1)
        #cv2.circle(bgr_acc_img, rb_pts.astype(np.int32), 2, (0,0,255), thickness=-1)

        #cv2.line(bgr_acc_img, lt_pts.astype(np.int32), rt_pts.astype(np.int32), (255,0,255), 1)
        #cv2.line(bgr_acc_img, rt_pts.astype(np.int32), rb_pts.astype(np.int32), (255,0,255), 1)
        #cv2.line(bgr_acc_img, rb_pts.astype(np.int32), lb_pts.astype(np.int32), (255,0,255), 1)
        #cv2.line(bgr_acc_img, lb_pts.astype(np.int32), lt_pts.astype(np.int32), (255,0,255), 1)
        #cv2.imshow('try four points', bgr_acc_img)
        #cv2.waitKey(0)
        top_k, top_dist = slope_dist(lt_pts, rt_pts)
        bot_k, bot_dist = slope_dist(lb_pts, rb_pts)
        left_k, left_dist = slope_dist(lt_pts, lb_pts)
        right_k, right_dist = slope_dist(rt_pts, rb_pts)
        #print('top k: {}, top_dist: {}'.format(top_k, top_dist))
        #print('bot k: {}, bot_dist: {}'.format(bot_k, bot_dist))
        #print('left k: {}, left_dist: {}'.format(left_k, left_dist))
        #print('right k: {}, right_dist: {}'.format(right_k, right_dist))
        if abs(top_dist-bot_dist) < epsilon_dst and abs(left_dist-right_dist) <epsilon_dst and \
                top_dist > 80 and bot_dist > 80 and left_dist > 80 and right_dist > 80 and \
                1-abs(cos_sim(lt_pts,rt_pts,lb_pts,rb_pts)) < epsilon_k and \
                1-abs(cos_sim(lt_pts,lb_pts,rt_pts,rb_pts)) < epsilon_k and \
                abs(cos_sim(lt_pts,rt_pts,rt_pts,rb_pts)) < epsilon_k and \
                abs(cos_sim(rb_pts,lb_pts,lb_pts,lt_pts)) < epsilon_k and \
                abs(top_dist-right_dist) < 0.3*top_dist and \
                abs(right_dist-bot_dist) < 0.3*right_dist and \
                abs(top_k) < epsilon_k :

        #if abs(top_dist - bot_dist) < epsilon_dst and abs(left_dist - right_dist) < epsilon_dst and \
        #        1 - abs(cos_sim(lt_pts, rt_pts, lb_pts, rb_pts)) < epsilon_k and \
        #        1 - abs(cos_sim(lt_pts, lb_pts, rt_pts, rb_pts)) < epsilon_k and \
        #        abs(cos_sim(lt_pts, rt_pts, rt_pts, rb_pts)) < epsilon_k and \
        #        abs(cos_sim(rb_pts, lb_pts, lb_pts, lt_pts)) < epsilon_k and \
        #        abs(top_k) < epsilon_k:
            # 1. 上下、左右边长之差
            # 2. 上下、左右平行度
            # 3. 相邻边长度关系
            # 4. 上边水平
            return np.array((lt_pts, rt_pts, rb_pts, lb_pts))
    return np.array(())








def search(src_img,  roi_size=512, board_size_range=[100,200,5], kernel_size=(99, 99), outer_diameter_range=(30, 99), ring_width_range=(5, 8), ring_threshold=[0.6,0.9,0.05],
           area_threshold=(2,1000), pts_type='avg', epsilon_k=0.15, epsilon_dst=30):
    """
    先从src_img找出ROI区域(search_roi_center), 然后在ROI区域找到ring(search_rings), 最后从可能的圆环圆心位置
    得到精确的4个圆心坐标(search_4_points)
    :param src_img:
    :param n: ROI中心点的时采样点,中心点为滤波后亮度最大区域的平均位置
    :param roi_size: ROI区域, (w, h)，太小可能标定板被截断，太大将会降低处理速度. -1 时跳过ROI，对全体图像进行检测，注意将会非常慢！
    :param board_size_range: 标定板可能尺寸范围
    :param kernel_size: 产生的滤波器将会被限制在该尺寸中
    :param outer_diameter_range: 环形可能的外经尺寸范围, 用于搜索环形特征
    :param ring_width_range: 环形可能的厚度尺寸范围
    :param ring_threshold: 对ROI区域进行环形过滤后，需要筛选最有可能的环形圆心区域，越大对环形越敏感，太小将包含噪声区域
    :param area_threshod: 对可能的环形圆心区域利用面积过滤，太大和太小的将会被filter out
    :param pts_type: 对面积符合要求的环形圆心可能位置进行中心点计算，可以使用平均法，也可以使用形心法
    :param epsilon_k: 对找到的所有点进行四边形搜索时，平行边和垂直边的最大斜率（垂直边斜率为倒数）
    :param epsilon_dst: 对找到的所有点进行四边形搜索时，对边的长度之差不能超过该值
    :return:
    """
    log = open('log.txt', 'a')
    log.write(f'[DEBUG] img mean: {np.mean(src_img)}, max: {np.max(src_img)}\n')

    #src_img = cv2.equalizeHist(src_img)
    src_img = src_img.astype(np.float32)
    src_img = src_img / 255.0
    #src_img = src_img + 0.4 * (src_img - np.mean(src_img))  # 左
    #cv2.imshow('enhanced', src_img)
    #padding 防止越界
    padding_board = roi_size // 2
    src_img = cv2.copyMakeBorder(src_img, padding_board, padding_board, padding_board, padding_board, borderType=cv2.BORDER_CONSTANT, value=0.0)
    #normalized_src_img = src_img / 255.0
    normalized_src_img = src_img

    if roi_size != 0:
        # 构造矩形滤波器 ，用于ROI选择
        kernels = generate_rect_kernels(rect_size=board_size_range, kernel_size=(200, 200))
        # 构造标定板四环滤波器
        #kernels = generate_board_kernels(1.0)
        # 滤波
        output = conv(normalized_src_img, kernels)
        roi_center_pos = search_ROI_center(output)  # 找到ROI中心点
        print(roi_center_pos)
        # ROI区域
        left_top_y = max(roi_center_pos[0] - roi_size // 2, 0)
        left_top_x = max(roi_center_pos[1] - roi_size // 2, 0)
        # 提取ROI
        roi_img = normalized_src_img[left_top_y:left_top_y+roi_size, left_top_x:left_top_x+roi_size]
    else:
        roi_img = normalized_src_img
        left_top_x = left_top_y = 0

    # 产生环形卷积核
    kernels = generate_ring_kernels(outer_diameter_range=outer_diameter_range, ring_width_range=ring_width_range, kernel_size=kernel_size)
    # GPU卷积
    roi_img = 1.0 - roi_img # 由于环形是黑色区域，但是我们希望反色，这样环形变成高亮区域，有助于理解卷积结果:卷积结果越亮，越可能是环形的圆心
    output = conv(roi_img, kernels)
    padding = (kernels[0].shape[0] - 1) // 2
    """
    由于不同标定板的光照环境变化剧烈，需要有一个阈值范围。ring_threshold越大，越对完美的环形敏感，相反越容易包含其他噪声。
    因此在设计时，先使用较大的阈值查找矩形，如果找不到再逐步降低阈值.
    """
    ring_threshold_beg, ring_threshold_end, step = ring_threshold
    nums = int((ring_threshold_end - ring_threshold_beg)/step) + 1
    #for a_ring_threshold in (np.arange(0, steps)*0.1 + ring_threshold_beg)[::-1]:
    for a_ring_threshold in np.linspace(ring_threshold_beg, ring_threshold_end, nums, endpoint=True)[::-1]:
        # 分析卷积结果, 越亮的位置越符合圆环圆心位置
        threshold_output = output > a_ring_threshold
        acc_img = None
        for i in range(threshold_output.shape[0]):
            if acc_img is None:
                acc_img = threshold_output[0]
            else:
                acc_img = acc_img | threshold_output[i] # 整合所有检查结果
            #cv2.imshow('filter', threshold_output[i].astype(np.uint8)*255)
            #cv2.imshow('output', np.array(output[i] * 255.0, dtype=np.uint8))
            #cv2.imshow('acc', np.array(acc_img, dtype=np.uint8)*255)
            #cv2.waitKey(33)
        acc_img = acc_img.astype(np.uint8)*255
        points = search_4_points(acc_img=acc_img, pts_type=pts_type, area_threshold=area_threshold)
        rect = search_rect(points=points, img=acc_img, epsilon_k=epsilon_k, epsilon_dst=epsilon_dst) # (x, y)
        if rect.size != 0:
            #LOG(log_types.OK, 'found rect.')
            return rect+np.array((-padding_board+left_top_x+padding, -padding_board+left_top_y+padding)) # 回到src_img的全局坐标系下

    #cv2.imshow('[WARN] No Rect Found!', bgr_roi_img)
    #LOG(log_types.NOTICE, 'no rect found.')
    return rect


#def search_batch(src_imgs,  roi_size=512, board_size_range=[100,200,5], kernel_size=(200, 200), outer_diameter_range=(30, 80), ring_width_range=(5, 8), ring_threshold=[0.5,0.8,0.05],
#           area_threshold=(2,1000), pts_type='avg', epsilon_k=0.5, epsilon_dst=15):
#    """
#    先从src_img找出ROI区域(search_roi_center), 然后在ROI区域找到ring(search_rings), 最后从可能的圆环圆心位置
#    得到精确的4个圆心坐标(search_4_points)
#    :param src_imgs: 多张输入图像
#    :param n: ROI中心点的时采样点,中心点为滤波后亮度最大区域的平均位置
#    :param roi_size: ROI区域, (w, h)，太小可能标定板被截断，太大将会降低处理速度. -1 时跳过ROI，对全体图像进行检测，注意将会非常慢！
#    :param board_size_range: 标定板可能尺寸范围
#    :param kernel_size: 产生的滤波器将会被限制在该尺寸中
#    :param outer_diameter_range: 环形可能的外经尺寸范围, 用于搜索环形特征
#    :param ring_width_range: 环形可能的厚度尺寸范围
#    :param ring_threshold: 对ROI区域进行环形过滤后，需要筛选最有可能的环形圆心区域，越大对环形越敏感，太小将包含噪声区域
#    :param area_threshod: 对可能的环形圆心区域利用面积过滤，太大和太小的将会被filter out
#    :param pts_type: 对面积符合要求的环形圆心可能位置进行中心点计算，可以使用平均法，也可以使用形心法
#    :param epsilon_k: 对找到的所有点进行四边形搜索时，平行边和垂直边的最大斜率（垂直边斜率为倒数）
#    :param epsilon_dst: 对找到的所有点进行四边形搜索时，对边的长度之差不能超过该值
#    :return:
#    """
#    imgs = []
#    for src_img in src_imgs:
#        src_img = cv2.equalizeHist(src_img)
#        cv2.imshow('qe', src_img)
#        cv2.waitKey(0)
#        src_img = src_img.astype(np.float32)
#        #padding 防止越界
#        padding_board = roi_size // 2
#        src_img = cv2.copyMakeBorder(src_img, padding_board, padding_board, padding_board, padding_board, borderType=cv2.BORDER_CONSTANT, value=0.0)
#        normalized_src_img = src_img / 255.0
#        imgs.append(normalized_src_img)
#    imgs = np.array(imgs)
#    imgs = torch.tensor(imgs).unsqueeze(1)
#
#    left_top_x = left_top_y = 0
#
#    # 产生环形卷积核
#    kernels = generate_ring_kernels(outer_diameter_range=outer_diameter_range, ring_width_range=ring_width_range, kernel_size=kernel_size)
#    # GPU卷积
#    roi_img = 1.0 - imgs # 由于环形是黑色区域，但是我们希望反色，这样环形变成高亮区域，有助于理解卷积结果:卷积结果越亮，越可能是环形的圆心
#    output = conv(roi_img, kernels)
#    #"""
#    #由于不同标定板的光照环境变化剧烈，需要有一个阈值范围。ring_threshold越大，越对完美的环形敏感，相反越容易包含其他噪声。
#    #因此在设计时，先使用较大的阈值查找矩形，如果找不到再逐步降低阈值.
#    #"""
#    res = []
#    for i, img in enumerate(output):
#        ring_threshold_beg, ring_threshold_end, step = ring_threshold
#        nums = int((ring_threshold_end - ring_threshold_beg)/step) + 1
#        rect = np.array(())
#        for a_ring_threshold in np.linspace(ring_threshold_beg, ring_threshold_end, nums, endpoint=True)[::-1]:
#            # 分析卷积结果, 越亮的位置越符合圆环圆心位置
#            threshold_output = img > a_ring_threshold
#            acc_img = None
#            for i in range(threshold_output.shape[0]):
#                if acc_img is None:
#                    acc_img = threshold_output[0]
#                else:
#                    acc_img = acc_img | threshold_output[i] # 整合所有检查结果
#                cv2.imshow('filter', threshold_output[i].astype(np.uint8)*255)
#                cv2.imshow('output', np.array(img[i] * 255.0, dtype=np.uint8))
#                cv2.imshow('acc', np.array(acc_img, dtype=np.uint8)*255)
#                cv2.waitKey(20)
#            acc_img = acc_img.astype(np.uint8)*255
#            points = search_4_points(acc_img=acc_img, pts_type=pts_type, area_threshold=area_threshold)
#            rect = search_rect(points=points, img=acc_img, epsilon_k=epsilon_k, epsilon_dst=epsilon_dst) # (x, y)
#            if rect.size != 0:
#                LOG(log_types.OK, 'found rect.')
#                res.append(rect+np.array((-padding_board+left_top_x, -padding_board+left_top_y))) # 回到src_img的全局坐标系下
#                break
#        #cv2.imshow('[WARN] No Rect Found!', bgr_roi_img)
#        if len(res) == i:
#            LOG(log_types.NOTICE, 'no rect found.')
#            res.append(rect)

#import pickle
#import codecs
#def parse_argv():
#    print(sys.argv[1])
#    src_img = np.array(pickle.loads(codecs.decode(sys.argv[1].encode(), 'base64')), dtype=np.float32)
#    print(src_img)
#    cv2.imshow('sdfsdf', src_img)
#    cv2.waitKey(0)
#    #search(src_img)
#
#
if __name__ == '__main__':
    print('hello')
    #img_path = 'C:/Users/xjtu/Downloads/Compressed/LeftCamera-228'
    src_img = 'C:/Users/001/Desktop/imgs/0.bmp'
    img_files = [src_img]
    for img in img_files:
        img = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
        cv2.imshow('d', img)
        cv2.waitKey(0)
        img = img[700:700+768, 300:300+768]
        cv2.imshow('img', img)
        cv2.waitKey(0)
        bgr_src = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        rect = search(src_img=img, roi_size=0)
        print(rect)
        if rect.any():
            cv2.line(bgr_src, rect[0].astype(np.int32), rect[1].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[1].astype(np.int32), rect[2].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[2].astype(np.int32), rect[3].astype(np.int32), (0, 255, 255), 1)
            cv2.line(bgr_src, rect[3].astype(np.int32), rect[0].astype(np.int32), (0, 255, 255), 1)
            cv2.imshow('found', bgr_src)
            cv2.waitKey(0)
        #search_batch(src_imgs=imgs, roi_size=0)

