"""
============
Author: Yifei Zhang
Email: imeafi@gmail.com

detect2.py文件提供了Detection_2方法的Qt封装
"""
import torch
from PyQt5.QtCore import QThread, pyqtSignal
from Modules.LOG import *
from Modules.Detection_2.predict import *

import numpy as np
import cv2


class Detection2(QThread):
    returnValSignal = pyqtSignal(str, np.ndarray)
    def __init__(self, cfg, description: str):
        super(Detection2, self).__init__()
        self.cfg = cfg
        self.imgs = None # Tensor (N,C,H,W) or None
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
        train_weights = self.cfg['Detection2_Conf']['WeightPath']
        root_path = os.getcwd()
        train_weights = os.path.join(root_path, train_weights)
        assert os.path.exists(train_weights), "{} file dose not exist.".format(train_weights)
        self.model.load_state_dict(torch.load(train_weights, map_location='cpu')['model'], strict=False)

        in_features = self.model.roi_heads.box_predictor.cls_score.in_features
        # replace the pre-trained head with a new one
        self.model.roi_heads.box_predictor = FastRCNNPredictor(in_features, 2)

        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([transforms.ToTensor()])


    def get_img(self, img):
        img = self.img_preprocess(img) # Tensor
        self.imgs = torch.cat((self.imgs, img), dim=0) if self.imgs is not None else img
        #self.imgs.append(img)


    def img_preprocess(self, img):
        """对单张ROI图像进行预处理：
        1. flip left-right and stack horizontally
        2. bgr -> rgb
        3. toTensor
        4. add batch channel
        """
        img = np.hstack((img, np.fliplr(img)))
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = self.transform(img)
        img = torch.unsqueeze(img, dim=0)
        return img


    def prediction_postprocess(self, image, outputs):
        """对神经网络输出进行解析
        :return:
        """
        for img, o in zip(image,outputs):
            img = 255 * (img.to('cpu').permute(1,2,0).numpy())
            boxes = o['boxes']
            scores = o['scores']
            #x = torch.ops.torchvision.nms(boxes, scores, 0.01)
            h, w, c = img.shape
            img = img[:, :w // 2, :]
            if o['boxes'].nelement() > 0:
                for b in boxes:
                    #bgr_img = np.tile(img, 3).astype(np.uint8)
                    bgr_img = img.astype(np.uint8)
                    b = b.to('cpu').numpy().astype(np.int32)
                    x1, y1, x2, y2 = b
                    if x1 > 768:
                        bgr_img = cv2.line(bgr_img, (2 * 768 - x1, y1), (2 * 768 - x2, y2), (255, 255, 0))
                    else:
                        bgr_img = cv2.line(bgr_img, (y1, x1), (y2, x1), (255,255,0))
                    cv2.imshow('line', bgr_img)
                    cv2.waitKey(1000)

    @torch.no_grad()
    def run(self):
        """
        备用检测逻辑: 首先使用缩小图进行快速的Rect检测，只有当存在rect时，再使用原图大小进行检测
        :return:
        """
        #rect = search(src_img=self.img, **self.kargs)
        while True:
            if self.imgs is not None:
                imgs = self.imgs.to(self.device)
                outputs = self.model(imgs)
                self.prediction_postprocess(imgs, outputs)
                self.imgs = None
                #self.returnValSignal.emit(self.descriotion, rect)  # 向CoreSystem发送检测结果，在system.py-detect()中绑定


if __name__ == '__main__':
    cfg = {'Detection2_Conf': {
     'WeightPath':'Detection_2/save_weights/resNetFpn-model-10.pth'
    }}
    det2 = Detection2(cfg=cfg, description='123')
    img_root = 'F:\Dataset\MyData\CL'
    #img = cv2.imread(img_root+'\left.png', cv2.IMREAD_GRAYSCALE)
    img = Image.open(img_root+'\\4.png')
    img = np.asarray(img)
    #img = img[800:1568, 2560-768:2560]
    #cv2.imshow('img', img)
    #cv2.waitKey(0)
    det2.get_img(img)
    det2.run()