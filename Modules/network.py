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
PORT = 6667
import queue



class AbstractMsg(QObject):
    # 向绑定用户发送控制字符以及数据，然后接受缓存
    NetworkCmdSignal = pyqtSignal(int, list, list)
    def __init__(self):
        """
        抽象数据包，用于维护接受和发送的数据包解析和发送工作.
        固定数据包为40字节
        """
        super(AbstractMsg, self).__init__()
        self.recCtlBits = np.uint32(0)
        self.recData = 6 * [np.float32(0.0)]
        self.recResBits = 3 * [np.uint32(0)]

        self.codenFormat_ = "I6f3I"

        # 解码时使用了大端序，最简单的方法是将接收到的二进制直接逆转，但此时数据结构也会逆转.
        self.decodenFormat_ = "3I6fI"


    def parse(self, data):
        if data and len(data) == 40:
            data = data[::-1]
            data = list(struct.unpack(self.decodenFormat_, data))
            self.recCtlBits, self.recData, self.recResBits = data[0], data[1:-3], data[-3:]
            print('[Info] Recv:', self.recCtlBits, self.recData, self.recResBits)
            self.NetworkCmdSignal.emit(self.recCtlBits, self.recData, self.recResBits)


    def pack(self, ctl, data, res):
        if data is None:
            data = 6 * [np.float32(0.0)]
        if ctl is None:
            ctl = np.uint32(0)
        if res is None:
            res = 3 * [np.uint32(0)]
        try:
            print('[Info] Pack:', ctl, data, res)
            DATA = namedtuple("DATA", "uCtl fData0 fData1 fData2 fData3 fData4 fData5 uRes0 uRes1 uRes2")
            msg_to_send = DATA(uCtl=ctl,
                               fData0=data[0],
                               fData1=data[1],
                               fData2=data[2],
                               fData3=data[3],
                               fData4=data[4],
                               fData5=data[5],
                               uRes0=res[0],
                               uRes1=res[1],
                               uRes2=res[2])
            msg_to_send = struct.pack(self.codenFormat_, *msg_to_send._asdict().values())
            return msg_to_send
        except Exception as e:
            pass
            print(e)


class Network(QThread):
    robotCommunicationStatusSignal = pyqtSignal(str)
    def __init__(self, ip, port):
        super(Network, self).__init__()
        self.ip = ip
        self.port = port
        # 解析报文内容
        self.msgManager = AbstractMsg()
        # 用于保存PLC连接的套接子，所有相关指令将通过该文件发送。读取并不需要单独管理.
        self.connectSocket = None
        self.lstCtl = None  # 上一次的指令
        self.lstData = None  # 上一次的数据，防止反复发送

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



    def send(self, ctl, data, res):
        sleep(0.5) # 注意如果没有这个，可能会导致缓存崩溃
        try:
            if self.connectSocket is not None: # 存在PLC链接
                msg_to_send = self.msgManager.pack(ctl, data, res)
                self.outputs.append(self.connectSocket)
                self.message_queues[self.connectSocket].put(msg_to_send)
            else:
                LOG(log_types.WARN, self.tr('No connection yet.'))
        except Exception as e:
            print(e.args[0])




from time import sleep
if __name__ == '__main__':
    app = QApplication(sys.argv)
    n = Network(ip='localhost', port=PORT)
    n.start()
    while True:
        n.send(ctl=12,data=None, res=None)
    sys.exit(app.exec())
