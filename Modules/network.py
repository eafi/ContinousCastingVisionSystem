import errno
import os
import select
import sys
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.Qt import QThread, QApplication
import socket
import numpy as np
from Modules.LOG import *
import struct
from collections import namedtuple
PORT = 6669
import queue



class AbstractMsg(QObject):
    # 向绑定用户发送控制字符以及数据，然后接受缓存
    NetworkCmdSignal = pyqtSignal(int, list)  # 在Robot.py中绑定,用于告知机器人状态
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
            self.NetworkCmdSignal.emit(self.recCtlBits, self.recData)


    def pack(self, ctl, data):
        if data is None:
            data = 9 * [np.float32(0.0)]
        if ctl is None:
            ctl = np.uint32(0)
        if not data == 9 * [np.float32(0)] or not ctl == np.uint32(0):
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


    def recv_clear(self):
        """
        成功接收后需要清空接收内容（在确定接受信号的对象接受到信号之后）
        :return:
        """
        self.recCtlBits = np.uint32(0)
        self.recCtlBits = 9 * [np.float32(0)]


class Network(QThread):
    robotCommunicationStatusSignal = pyqtSignal(str)
    def __init__(self, ip='localhost', port=PORT):
        super(Network, self).__init__()
        self.ip = ip
        self.port = port
        # 解析报文内容
        self.msgManager = AbstractMsg()
        # 用于保存PLC连接的套接子，所有相关指令将通过该文件发送。读取并不需要单独管理.
        self.connectSocket = None

    def run(self):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setblocking(0)  # 非阻塞套接字
                server.bind((self.ip, self.port))
                server.listen(1)
                inputs = [server]
                self.outputs = []
                self.message_queues = {}
                while inputs:
                    print('wating for the next event')
                    readable, writable, exceptional = select.select(inputs, self.outputs, inputs, 1)
                    for s in readable:
                        if s is server:
                            connection, client_address = s.accept()
                            print('connect from', client_address)
                            connection.setblocking(0)
                            inputs.append(connection)  # 同时监听这个新的套接子
                            self.message_queues[connection] = queue.Queue()
                            self.connectSocket = s
                            self.robotCommunicationStatusSignal.emit('OK')
                        else:
                            # 其他可读客户端连接
                            data = s.recv(40)
                            if data:
                                # 一个有数据的可读客户端
                                print('  received {!r} from {}'.format(
                                    data, s.getpeername()), file=sys.stderr)
                                #message_queues[s].put(data)
                                # 解析新来的数据，并保存到msgManager中
                                self.msgManager.parse(data)
                                #if s not in outputs:
                                #    outputs.append(s)
                            else: # 没有数据
                                print('closing', client_address)
                                self.robotCommunicationStatusSignal.emit('Break')
                                if s in self.outputs:
                                    self.outputs.remove(s)
                                inputs.remove(s)
                                s.close()

                                del self.message_queues[s]
                    for s in writable:
                        try:
                            next_msg = self.message_queues[s].get_nowait()
                        except queue.Empty:
                            print(' ', s.getpeername(), 'queue empty()')
                            self.outputs.remove(s)  # 该套接子没有要发送的内容，关闭套接子
                        else:
                            print(' sending {!r} to {}'.format(next_msg, s.getpeername()))
                            s.send(next_msg)

                    for s in exceptional:
                        print('exception conditon on', s.getpeername())
                        inputs.remove(s)
                        if s in self.outputs:
                            self.outputs.remove(s)
                        s.close()

                        del self.message_queues[s]



    def send(self, ctl, data=None):
        try:
            if self.connectSocket is not None:
                msg_to_send = self.msgManager.pack(ctl, data)
                self.outputs.append(self.connectSocket)
                self.message_queues[self.connectSocket].put(msg_to_send)
                print('[Info] Sent:', ctl, data)
            else:
                LOG(log_types.WARN, self.tr('No connection yet.'))
        except Exception as e:
            print(e)




from PyQt5.QtWidgets import QWidget, QTextEdit, QPushButton, QVBoxLayout
class Client(QWidget):
    def __init__(self, ip='localhost', port=6667):
        super(Client, self).__init__()
        self.net = Network()
        self.net.start()
        self.initUI()

    def initUI(self):
        self.sendTextbox = QTextEdit()
        self.sendTextbox.setText('12, 3.14, 23.4, 23, 56.7, 34.4, 7673.3, 456.3, 121.1, 23.2')
        self.btn = QPushButton('send')
        self.btn.clicked.connect(self.slot_btn)
        layout = QVBoxLayout()
        layout.addWidget(self.sendTextbox)
        layout.addWidget(self.btn)
        self.setLayout(layout)
        self.show()

    def slot_btn(self):
        txt = self.sendTextbox.toPlainText().split(',')
        if len(txt) < 10:
            print('[Error] Wrong typing.')
        elif len(txt) == 10:
            ctlBit = int(txt[0])
            data = [float(x) for x in txt[1:]]
            self.net.send(ctlBit, data)


from time import sleep
if __name__ == '__main__':
    app = QApplication(sys.argv)
    c = Client()
    sys.exit(app.exec())
