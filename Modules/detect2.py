"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

detect2.py文件提供了Detection_2方法的Qt封装
"""
from PyQt5.QtCore import QThread, pyqtSignal
from Modules.LOG import *
from Modules.Detection_2.predict import *

import numpy as np
import cv2


class Detection2(QThread):
    returnValSignal = pyqtSignal(str, np.ndarray)
    def __init__(self, cfg, description: str, img):
        super(Detection2, self).__init__()
        self.cfg = cfg
        self.img = img
        self.descriotion = description  # 用于描述这个img
        self.kargs = {}
        self.setup()


    def setup(self):
        """
        载入必要参数
        :return:
        """
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("using {} device.".format(self.device))

        # create model
        backbone = resnet50_fpn_backbone(norm_layer=torch.nn.BatchNorm2d,
                                         trainable_layers=3)
        # 训练自己数据集时不要修改这里的91，修改的是传入的num_classes参数
        self.model = FasterRCNN(backbone=backbone, num_classes=2)

        # load train weights
        train_weights = "./save_weights/resNetFpn-model-14.pth"
        assert os.path.exists(train_weights), "{} file dose not exist.".format(train_weights)
        self.model.load_state_dict(torch.load(train_weights, map_location=self.device)['self.model'])

        in_features = self.model.roi_heads.box_predictor.cls_score.in_features
        # replace the pre-trained head with a new one
        self.model.roi_heads.box_predictor = FastRCNNPredictor(in_features, 2)

        self.model.to(self.device)




    def run(self):
        """
        备用检测逻辑: 首先使用缩小图进行快速的Rect检测，只有当存在rect时，再使用原图大小进行检测
        :return:
        """
        #rect = search(src_img=self.img, **self.kargs)
        self.returnValSignal.emit(self.descriotion, rect)  # 向CoreSystem发送检测结果，在system.py-detect()中绑定
