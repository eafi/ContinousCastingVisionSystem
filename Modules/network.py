import errno
import os
import sys
from PyQt5.Qt import QThread, QApplication
import socket
import numpy as np
from LOG import *
import struct
from collections import namedtuple


class AbstractMsg:
    def __init__(self):
        self.ctlBits = np.uint32(0)
        self.data = 9 * [np.float32(0.0)]
        self.format_ = "I9f"


    def get(self):
        if self.empty():
            raise ValueError
        else:
            return bytearray(struct.pack('i', self.dataBits))+bytearray(struct.pack('f', self.dataBits[0]))

    def set(self, ctl: np.uint32, data: list):
        self.ctlBits = ctl
        self.data = data

    def recv(self, conn):
        try:
            data = conn.recv(40, 0x40)
        except BlockingIOError as e:
            data = None
        if data:
            data = list(struct.unpack(self.format_, data))
            self.ctlBits, self.data = data[0], data[1:]
            print('data:', self.ctlBits, self.data)
            #if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            #    print('No Data recv')
            #else:
            #    print(e)


    def send(self, socket):
        if not self.empty():
            try:
                DATA = namedtuple("DATA", "uCtl fData0 fData1 fData2 fData3 fData4 fData5 fData6 fData7 fData8")
                msg_to_send = DATA(uCtl=self.ctlBits,
                                   fData0=self.data[0],
                                   fData1=self.data[1],
                                   fData2=self.data[2],
                                   fData3=self.data[3],
                                   fData4=self.data[4],
                                   fData5=self.data[5],
                                   fData6=self.data[6],
                                   fData7=self.data[7],
                                   fData8=self.data[8])
                msg_to_send = struct.pack(self.format_, *msg_to_send._asdict().values())
                socket.sendall(msg_to_send)
            except Exception as e:
                pass
                print(e)


    def empty(self):
        return True if self.ctlBits == np.uint32(0) and self.data == 9 * [np.float32(0)] else False



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
            LOG(log_types.NOTICE, self.tr(f'Network connected with {addr}.'))
            with conn:
                #while True:
                    self.msgManager.recv(conn)
                    self.msgManager.send(conn)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    net = Network()
    net.start()
    sys.exit(app.exec())
