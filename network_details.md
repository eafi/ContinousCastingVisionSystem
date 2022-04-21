# 网络通讯协议及其实现细节

本文档用于详细描述视觉系统(包含视觉标定系统和视觉核心计算系统)
中所用通讯方式以及协议。

## 1 网络通讯总览

### 1.1 配置文件对网络的作用
视觉系统网络部分对应配置文件`CONF.cfg`的`Network_Conf`字段，
其中包括了网络监听IP地址，监听端口号，以及必要的通讯掩模字。

NOTE: 通讯掩模字与PLC沟通后落实，是网络协议的约定体现.

---

## 1.2 网络底层文件
NOTE: 网络底层提供了对PLC来回通讯的刷新和解码，通常不需要对
底层网络文件进行修改。对PLC解码后指令含义的进一步解释应该交由
其他文件，如`Modules.Robot`文件。

视觉系统的网络底层由`Modules.network`提供，该文件实现下述
功能：

1. 提供`Network`线程，用于监听连接、读取发送数据.
2. 本项目定义数据报为**40bytes**，因此不论是发送或是接受均以此单位读取.
3. 提供`AbstructMsg`类，用于对西门子PLC数据进行解码.

NOTE: APIS:

```python
# 需要发送的信息需要调用此函数
def send(ctl, data, res)
```
当读取PLC的信息时，使用`Network.ctlBit`, `Network.data`, `Network.resBit`进行读取.
这是因为在`Network`实现时，PLC不断发送信息，同时会刷新`Network`类的成员变量。因此可以直接
通过成员变量获得PLC信息。

## 1.3 视觉系统与PLC通讯媒介:ROBOT

NOTE: 当只关注功能扩展、功能实现，并不关注通讯底层时，只需关注`Modules.Robot`文件即可。
这是因为`Modules.Robot`作为视觉系统与PLC通讯的媒介，对通讯底层`Modules.Network`进一步
封装，并提供了更方便的函数接口。

```python
# 以Robot的一个开灯应用举例:
# 注意Configuration Manager非常重要，在本文档伊始提到通讯时
# 使用到了CONF.cfg的Network_Conf字段
cfgManager = CfgManager(path='../CONF.cfg')
cfg = cfgManager.cfg
robot = Robot(cfg=cfg)
robot.start()  # 启动
robot.set_light_on() # 开灯
```

上述为一个`Modules.Robot`的简单使用例程，使用Robot需要保证：
1. 提供配置文件信息，可使用自带的`Modules.parse.CfgManager`配合`CONF.cfg`实现
2. 产生一个`robot`实例，此时将与PLC建立连接，并开始网络通讯。(参见`Modules.Robot`构造函数).
3. 最后由于`Modules.Robot`已经依据`CONF.cfg`封装了通讯协议，并提供函数接口，因此直接调用以`set`开头的函数，传入必要参数，从而向PLC发送数据.

