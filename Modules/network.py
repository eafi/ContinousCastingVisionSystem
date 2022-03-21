import errno
import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.Qt import QThread, QApplication
import socket
import numpy as np
from Modules.LOG import *
import struct
from collections import namedtuple
PORT = 6669

class AbstractMsg(QObject):
    #newCmdSignal = pyqtSignal(int, list)
    def __init__(self):
        super(AbstractMsg, self).__init__()
        self.recCtlBits = np.uint32(0)
        self.recData = 9 * [np.float32(0.0)]
        self.format_ = "I9f"

    def parse(self, data):
        if data and len(data) == 40:
            data = list(struct.unpack(self.format_, data))
            self.recCtlBits, self.recData = data[0], data[1:]
            print('[Info] Recv:', self.recCtlBits, self.recData)
            #self.newCmdSignal.emit(self.msgManager.recCtlBits, self.msgManager.recData)
            # 向绑定用户发送控制字符以及数据，然后接受缓存
            return data


    def pack(self, ctl, data):
        if data is None:
            data = 9 * [np.float32(0.0)]
        if ctl is None:
            ctl = np.uint32(0)
        if not data == 9 * [np.float32(0)] and not ctl == np.uint32(0):
            try:
                DATA = namedtuple("DATA", "uCtl fData0 fData1 fData2 fData3 fData4 fData5 fData6 fData7 fData8")
                msg_to_send = DATA(uCtl=ctl,
                                   fData0=data[0],
                                   fData1=data[1],
                                   fData2=data[2],
                                   fData3=data[3],
                                   fData4=data[4],
                                   fData5=data[5],
                                   fData6=data[6],
                                   fData7=data[7],
                                   fData8=data[8])
                msg_to_send = struct.pack(self.format_, *msg_to_send._asdict().values())
                return msg_to_send
            except Exception as e:
                pass
                print(e)



    def set_send_data(self, ctlBit, data):
        self.sendCtlBits = ctlBit
        self.sendData = data


    def recv_clear(self):
        """
        成功接收后需要清空接收内容（在确定接受信号的对象接受到信号之后）
        :return:
        """
        self.recCtlBits = np.uint32(0)
        self.recCtlBits = 9 * [np.float32(0)]


class Network(QThread):
    robotCommunicationSignal = pyqtSignal(str)
    def __init__(self, ip='localhost', port=PORT):
        super(Network, self).__init__()
        self.ip = ip
        self.port = port
        # 解析报文内容
        self.msgManager = AbstractMsg()

    #TODO: 替换成seletct，当前网络代码没办法保证客户端断掉的检查
    def run(self):
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.bind((self.ip, self.port))
                    s.listen(1)
                    self.conn, addr = s.accept()  # 阻塞，等待链接
                    LOG(log_types.OK, self.tr(f'Network connected with {addr}.'))
                    self.robotCommunicationSignal.emit('OK')
                while True:
                    pass
            except Exception as e:
                self.robotCommunicationSignal.emit('Break')
                print('client is break!')


    def send(self, ctl, data=None):
        try:
            msg_to_send = self.msgManager.pack(ctl, data)
            self.conn.sendall(msg_to_send)
            print('[Info] Sent:', ctl, )
        except Exception as e:
            print(e)


    def recv(self):
        try:
            data = self.conn.recv(40)
        except BlockingIOError as e:
            data = None
        return self.msgManager.parse(data)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    net = Network()
    sys.exit(app.exec())
