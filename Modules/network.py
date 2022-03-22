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
    robotCommunicationStatusSignal = pyqtSignal(str)
    robotNewMsgignal = pyqtSignal(str)
    def __init__(self, ip='localhost', port=PORT):
        super(Network, self).__init__()
        self.ip = ip
        self.port = port
        # 解析报文内容
        self.msgManager = AbstractMsg()

    #TODO: 替换成select，当前网络代码没办法保证客户端断掉的检查
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setblocking(0)  # 非阻塞套接字
                server.bind((self.ip, self.port))
                server.listen(1)
                inputs = [server]
                outputs = []
                message_queues = {}
                while inputs:
                    print('wating for the next event')
                    readable, writable, exceptional = select.select(inputs, outputs, inputs)
                    self.robotCommunicationStatusSignal.emit('OK')
                    for s in readable:
                        if s is server:
                            connection, client_address = s.accept()
                            print('connect from', client_address)
                            connection.setblocking(0)
                            inputs.append(connection)  # 同时监听这个新的套接子

                            message_queues[connection] = queue.Queue()
                        else:
                            # 其他可读客户端连接
                            data = s.recv(40)
                            if data:
                                # 一个有数据的可读客户端
                                print('  received {!r} from {}'.format(
                                    data, s.getpeername()), file=sys.stderr,
                                )
                                self.msgManager.parse(data)
                                self.robotNewMsgignal.emit(data)
                                message_queues[s].put()
                                ## 添加到输出列表用来做响应
                                if s not in outputs:
                                    outputs.append(s)
                            else: # 没有数据
                                print('closing', client_address)
                                self.robotCommunicationStatusSignal.emit('Break')
                                if s in outputs:
                                    outputs.remove(s)
                                inputs.remove(s)
                                s.close()

                                del message_queues[s]
                    for s in writable:
                        try:
                            next_msg = message_queues[s].get_nowait()
                        except queue.Empty:
                            print(' ', s.getpeername(), 'queue empty()')
                            outputs.remove(s)  # 该套接子没有要发送的内容，关闭套接子
                        else:
                            print(' sending {!r} to {}'.format(next_msg, s.getpeername()))
                            s.send(next_msg)

                    for s in exceptional:
                        print('exception conditon on', s.getpeername())
                        inputs.remove(s)
                        if s in outputs:
                            outputs.remove(s)
                        s.close()

                        del message_queues[s]

        except Exception as e:
            self.robotCommunicationStatusSignal.emit('Break')
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
    net.start()
    sys.exit(app.exec())
