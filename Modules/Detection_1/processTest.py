import argparse
import numpy as np
import cv2
import sys


def main() :
    #parse = argparse.ArgumentParser()
    #parse.add_argument('--src_img', default='sdfsdf',type=str, required=True)
    #parse.add_argument('--roi_size', type=int, default=0, help='Find sub ROI in img. 0 for disable. ')
    #parse.add_argument('--board_size_range', type=list, default=[100,200,5], help='The expected board size range.')
    #parse.add_argument('--kernel_size', type=tuple, default=(200,200), help='max size of kernel.')
    #parse.add_argument('--outer_diameter_range', type=tuple, default=(30,80), help='The expected outer ring diameter')
    #parse.add_argument('--ring_width_range', type=tuple, default=(5,8), help='The expected ring width range.')
    #parse.add_argument('--ring_threshold', type=list, default=[0.5,0.8,0.05], help='Filter the conv and find the ring center.')
    #parse.add_argument('--area_threshold', type=tuple, default=(2, 10000) , help='Connected Component Threshold.')
    #parse.add_argument('--pts_type', type=str, default='avg' , help='Fitting the ring center via average or centroids.')
    #parse.add_argument('--epsilon_k', type=float, default=0.5, help='Define max horizontal slope.')
    #parse.add_argument('--epsilon_dst', type=float, default=15)

    #args = parse.parse_args()
    #print(args)
    #import pickle
    #import codecs
    #src_img = np.array(pickle.loads(codecs.decode(args.src_img.encode(), 'base64')), dtype=np.float32)
    src_img = 'sft.png'
    print(src_img)
    print(sys.argv)

if __name__ == '__main__':
    main()