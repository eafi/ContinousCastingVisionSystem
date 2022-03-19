import errno
import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.Qt import QThread, QApplication
import socket
import numpy as np
from LOG import *
import struct
from collections import namedtuple


class AbstractMsg(QObject):
    newCmdRecSignle = pyqtSignal(int, str)
    def __init__(self):
        self.recCtlBits = np.uint32(0)
        self.recData = 9 * [np.float32(0.0)]
        self.sendCtlBits = np.uint32(0)
        self.sendData = 9 * [np.float32(0.0)]
        self.format_ = "I9f"

    def recv(self, conn):
        try:
            data = conn.recv(40, 0x40)
        except BlockingIOError as e:
            data = None
        if data and len(data) == 40:
            print(data)
            data = list(struct.unpack(self.format_, data))
            self.recCtlBits, self.recData = data[0], data[1:]
            print('data:', self.recCtlBits, self.recData)
            # 向绑定用户发送控制字符以及数据，然后接受缓存
            self.newCmdRecSignle.emit(self.recCtlBits, self.recData)
            self.recv_clear()


    def send(self, socket):
        if not self.empty():
            try:
                DATA = namedtuple("DATA", "uCtl fData0 fData1 fData2 fData3 fData4 fData5 fData6 fData7 fData8")
                msg_to_send = DATA(uCtl=self.sendCtlBits,
                                   fData0=self.sendData[0],
                                   fData1=self.sendData[1],
                                   fData2=self.sendData[2],
                                   fData3=self.sendData[3],
                                   fData4=self.sendData[4],
                                   fData5=self.sendData[5],
                                   fData6=self.sendData[6],
                                   fData7=self.sendData[7],
                                   fData8=self.sendData[8])
                msg_to_send = struct.pack(self.format_, *msg_to_send._asdict().values())
                socket.sendall(msg_to_send)
                self.send_clear()
            except Exception as e:
                pass
                print(e)


    def empty(self):
        return True if self.sendCtlBits == np.uint32(0) and self.sendData == 9 * [np.float32(0)] else False

    def recv_clear(self):
        """
        成功接收后需要清空接收内容（在确定接受信号的对象接受到信号之后）
        :return:
        """
        self.recCtlBits = np.uint32(0)
        self.recCtlBits = 9 * [np.float32(0)]

    def send_clear(self):
        """
        成功发送后需要清空发送内容
        :return:
        """
        self.sendCtlBits = np.uint32(0)
        self.sendData = 9 * [np.float32(0)]


# TODO: 增加命令解析class解析RecvData指令。 从而控制Coresystem观察并运算哪一个ROI?
class Network(QThread):
    def __init__(self):
        super(Network, self).__init__()
        self.msgManager = AbstractMsg()


    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 6667))
            s.listen(1)
            conn, addr = s.accept()  # 阻塞，等待链接
            print('wait to be connected.')
            LOG(log_types.OK, self.tr(f'Network connected with {addr}.'))
            with conn:
                while True:
                    self.msgManager.recv(conn)
                    self.msgManager.send(conn)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    net = Network()
    net.start()
    sys.exit(app.exec())
