import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QMessageBox, QComboBox, QTextEdit
import numpy as np
from Modules.parse import CfgManager
from Modules.parse import write_couple_cfg

class TargetCircle(QWidget):
    """
    当机器人TCP变化时，用于补偿y轴的拟合圆半径发生了变化，此时需要重新拟合。
    拟合方法为，选择需要拟合的目标物体，输入两个以上的成功安装的示教器上X Y坐标
    该拟合结果将会覆盖CONF文件
    """
    def __init__(self, cfg):
        super(TargetCircle, self).__init__()
        self.cfg = cfg
        self.cfg_target_circle_dict = self.cfg['TargetCircle_Conf']
        self.init_gui()

    def init_gui(self):
        layout = QVBoxLayout()
        self.combox = QComboBox()
        self.combox.addItems(self.cfg_target_circle_dict.keys())
        self.combox.currentTextChanged.connect(self.slot_select_change)

        self.xyr_label1 = QLabel(self.tr('Current [圆心X mm] [圆心Y mm] [半径R mm]'))
        self.xyr_label2 = QLabel(self.tr('0,0,0'))
        self.xy_edit_info_label = QLabel(self.tr('input X,Y:'))
        self.new_xy_edit = QTextEdit()
        self.new_circle_btn = QPushButton(self.tr('New Circle'))
        self.new_circle_btn.clicked.connect(self.slot_new_circle_btn)
        self.show_xyr()
        layout.addWidget(self.combox)
        layout.addWidget(self.xyr_label1)
        layout.addWidget(self.xyr_label2)
        layout.addWidget(self.new_xy_edit)
        layout.addWidget(self.new_circle_btn)
        self.setLayout(layout)

    def show_xyr(self):
        xyr = self.cfg_target_circle_dict[self.combox.currentText()]
        self.xyr_label2.setText(self.tr(str(xyr)))

    def slot_select_change(self, idx):
        self.show_xyr()

    def slot_new_circle_btn(self):
        txt = self.new_xy_edit.toPlainText()
        pts_xy = self.pts_checker(txt)
        if pts_xy is None:
            return
        # 利用当前的圆的圆心，拟合出全新的半径，并覆盖掉原来的半径
        cxcycr = self.cfg_target_circle_dict[self.combox.currentText()]
        cxcy = cxcycr[:2]
        print(pts_xy - cxcy)
        rs = []
        for pt_xy in pts_xy:
            x, y = pt_xy
            cx, cy = cxcy
            new_r = np.sqrt((x-cx)*(x-cx) + (y-cy)*(y-cy))
            rs.append(new_r)
        print(rs)
        avg_r = np.mean(rs)

        ret = QMessageBox.warning(self, 'Warning!', f'The circle radius of'
                                                    f' {self.combox.currentText()}'
                                                    f'will be changed from '
                                                    f'{cxcycr[-1]} mm to '
                                                    f'{rs} mm,\n'
                                                    f'avg:{avg_r} mm', QMessageBox.No, QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            # 覆盖半径
            new_str_cxcycr = '{:.4f},{:.4f},{:.4f}'.format(cxcy[0], cxcy[1], avg_r)
            write_couple_cfg((self.combox.currentText(), new_str_cxcycr), '../CONF.cfg')
            # 刷新当前内存中的cfg，用于界面显示
            new_cxcycr = cxcy
            new_cxcycr.append(avg_r)
            self.cfg['TargetCircle_Conf'][self.combox.currentText()] = new_cxcycr
            self.show_xyr()
            print('Done!')
            self.new_xy_edit.clear()


    def pts_checker(self, txt):
        try:
            txt = txt.strip()
            txt = txt.replace('\n', ',')
            txt = txt.split(',')
            txt = [float(x) for x in txt]
            txt = np.array(txt).reshape(-1,2)
            return txt
        except Exception as e:
            print('Failed.')
            return None


if __name__ == '__main__':
    cfg = {
        'TargetCircle_Conf':
            {
                'NozzleCircle':'10,10,10',
                'PowerEndCircle': '-173.79198, -5005.76502,10'
            }
    }
    d = cfg['TargetCircle_Conf']
    for key in d.keys():
        cfg['TargetCircle_Conf'][key] = [float(x) for x in d[key].split(',')]
    app = QApplication(sys.argv)
    ex = TargetCircle(cfg)
    ex.show()
    sys.exit(app.exec())
