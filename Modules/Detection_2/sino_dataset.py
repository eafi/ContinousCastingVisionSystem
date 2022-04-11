from torch.utils.data import Dataset
import torch
from PIL import Image
import numpy as np


class SinoDataSet(Dataset):

    def __init__(self, img_list, annotation_list, transforms = None):
        self.img_list = img_list
        self.annotation_list = annotation_list
        self.transforms = transforms


    def __len__(self):
        return len(self.img_list)


    def __getitem__(self, idx):
        img_file = self.img_list[idx]
        target_file = self.annotation_list[idx]
        image = Image.open(img_file)
        image_np = np.asarray(image)
        image = np.hstack((image_np, np.fliplr(image_np)))
        image = Image.fromarray(image)
        f = open(target_file, 'r')
        line = [float(x) for x in f.readline().split(' ')]
        f.close()
        target = {}
        target['labels'] = [line[0], line[0]]
        if len(line) == 1:
            target['boxes'] = [[np.float32(0)] * 4, [np.float32(0)] * 4]
        else:
            target['boxes'] = [[line[1], line[2], line[5], line[6]],[2*768-line[3], line[4], 2*768-line[7], line[8]]]
        target['boxes'] = torch.as_tensor(target['boxes'], dtype=torch.float32)
        target['labels'] = torch.as_tensor(target['labels'], dtype=torch.int64)
        if self.transforms is not None:
            image, target = self.transforms(image, target)

        return image, target


    def get_height_and_width(self, idx):
        return 768, 768

    @staticmethod
    def collate_fn(batch):
        return tuple(zip(*batch))

