# -*- coding: utf-8 -*-

__all__ = ['PIPZTController', 'showPortInfo', 'AMCPZTController']

from abc import abstractmethod, ABCMeta
import serial.tools.list_ports
from textwrap import dedent
import time
import threading
from platform import architecture
import importlib.util
import os

class OutOfRange(Exception):
    """
    The target position is larger than the movable range of the piezoelectric guide.
    """

def showPortInfo():
    """
    查看串口的信息
    :return: 打印串口信息，返回串口的个数
    """
    port_list = list(serial.tools.list_ports.comports())
    if len(port_list) <= 0:
        print('The Serial port can"t find!')
        return 0
    else:
        print('check port')
        print(port_list)
        return len(port_list)

class PZTController(metaclass=ABCMeta):
    """
    PZT控制器抽象类，具体方法需要实现。

    proprety:
        device-目标设备对象
        _info-字典类型，保存设备对象主要信息
        _lock-锁，保证多线程安全
        _moveState-移动状态

    method:
        __init__-初始化
        isOpen-判断设备是否打开
        isMoving-判断是否在移动
        getStartPosition-返回目标设备的初始位置
        getRange-返回PZT的行程
        getInit-返回初始化信息
        getInfo-返回需要实时更新的信息
        getAllInfo-返回所有信息
        setAllInfo-设置实时更新的信息
        setStartPosition-设置初始位置
        getPosition-获得当前的位置
        getDeviation-获得当前位置距离设备的偏移
        move-以绝对坐标的形式移动到目标位置
        do-恢复距离初始位置的偏移量
        close-关闭物理设备
    """

    def __init__(self):
        self.device = None
        self._info = {'numaxes': None,
                      'startPosition': None,
                      'range': [],
                      'position': None,
                      'deviation': None}
        self._moveState = None
        self._lock = threading.RLock()

    # 返回初始位置
    def reset(self):
        with self._lock:
            if not self.device:
                return
            self.move(self.getStartPosition())

    def isMoving(self):
        return self._moveState

    def isOpen(self):
        with self._lock:
            if not self.device:
                return False
            else:
                return True

    def getStartPosition(self):
        return self._info['startPosition']

    def getRange(self):
        return self._info['range']

    def getInit(self):
        with self._lock:
            return {'numaxes': self._info['numaxes'],
                    'startPosition': self.getStartPosition(),
                    'range': self.getRange()}

    def getInfo(self):
        with self._lock:
            return {'position': self.getPosition(),
                    'deviation': self.getDeviation()}

    def getAllInfo(self):
        with self._lock:
            return self.getInit().update(self.getInfo())

    def setAllInfo(self, info):
        with self._lock:
            info.pop('numaxes', None)
            info.pop('range', None)
            self._info.update(info)
            self.setStartPosition(self._info['startPosition'])
            self.move(self._info['position'])

    @abstractmethod
    def setStartPosition(self, start):
        pass

    @abstractmethod
    def getPosition(self):
        pass

    @abstractmethod
    def getDeviation(self, centers=None):
        pass

    @abstractmethod
    def move(self, targets):
        pass

    @abstractmethod
    def do(self, deviations):
        pass

    @abstractmethod
    def close(self):
        pass

try:
    from pipython import GCSDevice, pitools

    def connectPIMachine(name, stages, refmode, mode, **kwargs):
        """
        连接PI设备具有三种方式
        :param name: 控制器的名称
        :param stages: 控制器管理的平台
        :param refmode:
        :param mode: 连接的模式，可以为RS232，USB，TCPIP
        :param kwargs: 对应连接模式下具体的参数
        :return: 返回目标设备对象
        """
        dllname = 'PI_GCS2_DLL'
        if architecture()[0] == '64bit':
            dllname += '_x64'
        dllname += '.dll'
        if dllname in os.listdir(os.getcwd()):
            pidevice = GCSDevice(name, os.path.join(os.getcwd(), dllname))
        else:
            pidevice = GCSDevice(name)
        if mode == 'RS232':
            pidevice.ConnectRS232(comport=kwargs['comport'], baudrate=kwargs['baudrate'])
        elif mode == 'USB':
            pidevice.ConnectUSB(serialnum=kwargs['serialnum'])
        elif mode == 'TCPIP':
            pidevice.ConnectTCPIP(ipaddress=kwargs['ipaddress'])
        else:
            print(dedent('''
            specify a mode "RS232", "USB", "TCPIP"
            # pidevice.ConnectRS232(comport=1, baudrate=115200)
            # pidevice.ConnectUSB(serialnum='123456789')
            # pidevice.ConnectTCPIP(ipaddress='192.168.178.42')
            '''))
            return
        print('connected: {}'.format(pidevice.qIDN().strip()))
        # print('initialize connected stages...')
        # pitools.startup(pidevice, stages=stages, refmode=refmode)
        return pidevice

    class PIPZTController(PZTController):
        """
        PI版本的PZT控制器，继承了Controller类型。

        proprety:
            device-目标设备对象
            _info-字典类型，保存设备对象主要信息
            name-目标设备对象的本地名称
            _lock-锁，保证多线程安全

        method:
            __init__-初始化
            connect-连接PI设备
            init-初始化，获得物理设备的具体参数
            isOpen-判断设备是否打开
            setStartPosition-设置初始位置
            getPosition-获得当前的位置
            getDeviation-获得当前位置距离设备的偏移
            move-以绝对坐标的形式移动到目标位置
            do-恢复距离初始位置的偏移量
            close-关闭物理设备
        """

        def __init__(self, name, *args, **kwargs):
            super(PIPZTController, self).__init__()
            self.name = name

        def connect(self, controllername, stages, refmode, mode, **kwargs):
            with self._lock:
                if self.device:
                    return
                self.device = connectPIMachine(controllername, stages, refmode, mode, **kwargs)
                self._info['numaxes'] = self.device.numaxes
                self._moveState = False
                self.init()

        # 获得基本参数
        def init(self):
            with self._lock:
                rangemin = list(self.device.qTMN().values())
                print('min range for each axis is: {}'.format(str(rangemin)))
                rangemax = list(self.device.qTMX().values())
                print('max range for each axis is: {}'.format(str(rangemax)))
                # 总行程
                self._info['range'] = tuple(zip(rangemin, rangemax))
                self.setStartPosition()

        def setStartPosition(self, start=None):
            with self._lock:
                if not self.device:
                    return
                if not start:
                    # 开始位置
                    self._info['startPosition'] = self.getPosition()
                    print('start pos is: {}'.format(str(self._info['startPosition'])))
                else:
                    if len(start) != self._info['numaxes']:
                        raise TypeError('The number of axes set is not equal to the number of axes of the device.')
                    else:
                        self.move(start)
                        self._info['startPosition'] = self.getPosition()
                        print('start pos is: {}'.format(str(self._info['startPosition'])))

        def getPosition(self):
            with self._lock:
                if not self.device:
                    return
                r = self.device.qPOS(self.device.axes)
                rt = []
                for i in range(self._info['numaxes']):
                    rt.append(r[str(i + 1)])
                return tuple(rt)

        def getDeviation(self, centers=None):
            with self._lock:
                if not self.device:
                    return
                if centers is None:
                    centers = self._info['startPosition']
                deviation = []
                pos = self.getPosition()
                for ind, p in enumerate(pos):
                    deviation.append(p - centers[ind])
                return tuple(deviation)

        def move(self, targets, timeout=60):
            with self._lock:
                try:
                    self._moveState = True
                    if not self.device:
                        raise SystemError('No available device.')
                    for i in self.device.axes:
                        i = int(i) - 1
                        if targets[i] > self._info['range'][i][1] or targets[i] < self._info['range'][i][0]:
                            raise OutOfRange('Sorry, out of range in axis {}'.format(str(i)))
                    print('{} targets: {}'.format(str(self.name), str(targets)))
                    self.device.MOV(self.device.axes, targets)
                    pitools.waitontarget(self.device, timeout=timeout)
                    self._moveState = False
                except SystemError:
                    self._moveState = None
                    self.close()
                    raise
                except:
                    self._moveState = False
                    raise

        def do(self, deviations, centers=None):
            with self._lock:
                if not self.device:
                    return
                if centers is None:
                    centers = self._info['startPosition']
                targets = [float(y - x) for x, y in zip(deviations, centers)]
                self.move(targets)

        def close(self):
            with self._lock:
                if not self.device:
                    return
                try:
                    self.device.close()
                except Exception as e:
                    print(str(e))
                finally:
                    self.device = None

        def __del__(self):
            print('关闭PI压电:{}'.format(self.name))
            self.close()

except ImportError:
    print('Warning: No module name pipython')
    PIPZTController = None

try:
    import fcre._extern.AMC as AMC

    class amctools:

        @staticmethod
        def waitontarget(device, axis, timeout):
            maxtime = time.time() + timeout
            while True:
                sts = []
                errno, status = AMC.getStatusMoving(device, axis)
                if errno:
                    raise SystemError('System error! Please reconnect the device.')
                else:
                    sts.append(status==1)  # status == 1 for moving status
                if any(sts):
                    if time.time() > maxtime:
                        raise SystemError('waitontarget() timed out after %.1f seconds' % timeout)
                    time.sleep(0.1)
                else:
                    break

    class AMCPZTController(PZTController):
        """
        AMC版本的PZT控制器，继承了Controller类型。

        proprety:
            device-目标设备对象
            _info-字典类型，保存设备对象主要信息
            name-目标设备对象的本地名称
            _lock-锁，保证多线程安全

        method:
            __init__-初始化
            connect-连接AMC设备
            init-初始化，获得物理设备的具体参数
            isOpen-判断设备是否打开
            setStartPosition-设置初始位置
            getPosition-获得当前的位置
            getDeviation-获得当前位置距离设备的偏移
            move-以绝对坐标的形式移动到目标位置
            do-恢复距离初始位置的偏移量
            close-关闭物理设备
        """

        def __init__(self, name, *args, **kwargs):
            super(AMCPZTController, self).__init__()
            self.name = name

        def connect(self, numaxes, ip='192.168.1.1', *args, **kwargs):
            with self._lock:
                if self.device:
                    return
                self.device = AMC.connect(ip)
                self._info['numaxes'] = numaxes
                for i in range(self._info['numaxes']):
                    # AMC.setReset(self.device, i)
                    AMC.setOutput(self.device, i, 'true')
                    time.sleep(0.1)
                self._moveState = False
                self.init()

        def init(self):
            with self._lock:
                _ranges = []
                for i in range(self._info['numaxes']):
                    # To clearly indentify the range of PZT
                    _range = (-5000000, 5000000)  # need repairs!!
                    print('range for each axis {} is: {}'.format(str(i), str(_range)))
                    _ranges.append(_range)
                # 总行程
                self._info['range'] = _ranges
                self.setStartPosition()

        def setStartPosition(self, start=None):
            with self._lock:
                if not self.device:
                    return
                if not start:
                    # 开始位置
                    self._info['startPosition'] = [AMC.getPosition(self.device, i)[1] for i in
                                                   range(self._info['numaxes'])]
                    print('start pos is: {}'.format(str(self._info['startPosition'])))
                else:
                    if len(start) != self._info['numaxes']:
                        raise TypeError('The number of axes set is not equal to the number of axes of the device.')
                    else:
                        self._info['startPosition'] = start
                        print('start pos is: {}'.format(str(self._info['startPosition'])))
                for ind, target in enumerate(self._info['startPosition']):
                    AMC.setTargetPosition(self.device, ind, target)
                    # AMC.setMove(self.device, ind, 'true')
                    # time.sleep(0.5)

        def getPosition(self):
            with self._lock:
                if not self.device:
                    return
                pos = [AMC.getPosition(self.device, i)[1] for i in range(self._info['numaxes'])]
                self._info['position'] = pos
                return tuple(pos)

        def getDeviation(self, centers=None):
            with self._lock:
                if not self.device:
                    return
                if centers is None:
                    centers = self._info['startPosition']
                deviation = []
                pos = self.getPosition()
                for ind, p in enumerate(pos):
                    deviation.append(p - centers[ind])
                self._info['deviation'] = deviation
                return tuple(deviation)

        def move(self, targets, timeout=60):
            with self._lock:
                try:
                    self._moveState = True
                    if not self.device:
                        raise SystemError('No available device.')
                    targets = [int(t) for t in targets]
                    for i in range(self._info['numaxes']):
                        if targets[i] > self._info['range'][i][1] or targets[i] < self._info['range'][i][0]:
                            raise OutOfRange('Sorry, out of range in axis {}'.format(str(i)))
                    print('{} targets: {}'.format(str(self.name), str(targets)))
                    for ind, target in enumerate(targets):
                        AMC.setTargetPosition(self.device, ind, target)
                        AMC.setMove(self.device, ind, 'true')
                    for ind in range(self._info['numaxes']):
                        amctools.waitontarget(self.device, ind, timeout)
                    self._moveState = False
                except SystemError:
                    self._moveState = None
                    self.close()
                    raise
                except:
                    self._moveState = False
                    raise

        def do(self, deviations, centers=None):
            with self._lock:
                if not self.device:
                    return
                if centers is None:
                    centers = self._info['startPosition']
                targets = [float(y - x) for x, y in zip(deviations, centers)]
                self.move(targets)

        def close(self):
            with self._lock:
                if not self.device:
                    return
                try:
                    for i in range(self._info['numaxes']):
                        AMC.setMove(self.device, i, 'false')
                        time.sleep(0.1)
                        AMC.setOutput(self.device, i, 'false')
                        time.sleep(0.1)
                    AMC.close(self.device)
                except Exception as e:
                    print(str(e))
                finally:
                    self.device = None

        def __del__(self):
            print('关闭AMC压电:{}'.format(self.name))
            self.close()

except ImportError:
    print('Warning: No module name AMC')
    AMCPZTController = None
