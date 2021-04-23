# -*- coding: utf-8 -*-

__all__ = ['PIPZTController', 'showPortInfo', 'AMCPZTController']

import os
import importlib.util
from abc import abstractmethod, ABCMeta
from textwrap import dedent
import time
import threading
from platform import architecture
import copy

import serial.tools.list_ports

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
        return copy.deepcopy(self._info['startPosition'])

    def getRange(self):
        return copy.deepcopy(self._info['range'])

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
                self.init()

        # 获得基本参数
        def init(self):
            with self._lock:
                self._info['numaxes'] = self.device.numaxes
                self._moveState = False
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
                        raise TypeError('The number of axes set is not equal to the' 
                                            'number of axes of the device.')
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
                if len(targets) != self._info['numaxes']:
                    raise TypeError('The number of axes set is not equal to the' 
                                    'number of axes of the device.')
                try:
                    self._moveState = True
                    if not self.device:
                        raise SystemError('No available device.')
                    for i in self.device.axes:
                        i = int(i) - 1
                        _range = self._info['range'][i]
                        if (targets[i] > _range[1]) or (targets[i] < _range[0]):
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
        def waitontarget(device, axis, timeout=60, eottimeout=1):
            maxtime = time.time() + timeout
            target_range = AMC.getTargetRange(device, axis)[1]
            target_pos = AMC.getTargetPosition(device, axis)[1]

            # eot detection
            max_interval = int(eottimeout/0.1) + 1
            last_pos = AMC.getPosition(device, axis)[1]
            i_interval = 0

            while True:
                errno, status = AMC.getStatusMoving(device, axis)
                if errno:
                    raise SystemError('System error! Please reconnect the device.')

                if status == 1: # status == 1 for moving status

                    pos = AMC.getPosition(device, axis)[1]
                    if abs(pos - target_pos) < target_range:
                        AMC.setMove(device, axis, False)
                        break

                    # no-blocking End of Travel detection
                    if i_interval != max_interval:
                        i_interval += 1
                    else:
                        i_interval = 0
                        
                        pos = AMC.getPosition(device, axis)[1]
                        if abs(last_pos - pos) < target_range:
                            AMC.setMove(device, axis, False)
                            return False
                        last_pos = pos

                    if time.time() > maxtime:
                        raise SystemError('waitontarget() timed out after %.1f seconds' % timeout)
                    time.sleep(0.1)
                else:
                    break
            
            return True


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

        def connect(self, ip='192.168.1.1', *args, **kwargs):
            with self._lock:
                if self.device:
                    return
                self.device = AMC.connect(ip)
                self.init()

        def init(self):
            with self._lock:
                for i in range(3):  # AMC can only control axis [0..2]
                    if AMC.setOutput(self.device, i, True) != 0:
                        break
                    else:
                        AMC.setMove(self.device, i, False)
                self._info['numaxes'] = i
                self._moveState = False

                # End of Travel detection
                for i in range(self._info['numaxes']):
                    AMC.setEotOutputDeactive(self.device, i, True)

                # 总行程
                self._info['range'] = [(None,None), (None,None)]
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
                        raise TypeError('The number of axes set is not equal to the' \
                                        'number of axes of the device.')
                    else:
                        self.move(start)
                        self._info['startPosition'] = [AMC.getPosition(self.device, i)[1] for i in
                                                      range(self._info['numaxes'])]
                        print('start pos is: {}'.format(str(self._info['startPosition'])))

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

        def move(self, targets, timeout=60, eottimeout=1):
            with self._lock:
                if len(targets) != self._info['numaxes']:
                    raise TypeError('The number of axes set is not equal to the' 
                                    'number of axes of the device.')
                try:
                    self._moveState = True
                    if not self.device:
                        raise SystemError('No available device.')

                    # out of range judgement
                    targets = [int(t) for t in targets]
                    for i in range(self._info['numaxes']):
                        _range = self._info['range'][i]
                        if (None not in _range):
                            if (targets[i] > _range[1]) or (targets[i] < _range[0]):
                                raise OutOfRange('Sorry, out of range in axis {}'.format(str(i)))
                        else:
                            continue
                    
                    #　move to targets
                    print('{} targets: {}'.format(str(self.name), str(targets)))
                    for i, target in enumerate(targets):
                        AMC.setTargetPosition(self.device, i, target)
                        AMC.setMove(self.device, i, True)
                    
                    # wait
                    states = [None] * self._info['numaxes']
                    for i in range(self._info['numaxes']):
                        states[i] = amctools.waitontarget(self.device, i, timeout, eottimeout)
                    self._moveState = False
                    
                    # update range!
                    if not all(states):
                        err_info = "" 
                        for i, state in enumerate(states):
                            if not state:
                                pos = AMC.getPosition(self.device, i)[1]
                                _range = list(self._info['range'][i])
                                if pos < targets[i]:
                                    _range[1] = pos
                                else:
                                    _range[0] = pos
                                self._info['range'][i] = tuple(_range)
                                print('range for axis {} is: {}'.format(str(i), str(_range)))
                                err_info += 'Sorry, out of range in axis {}. ' \
                                        'Position {} Range {}\n'.format(str(i), str(pos), str(_range))
                        raise OutOfRange(err_info)

                except SystemError:
                    self._moveState = None
                    self.close()
                    raise
                except:
                    for i in range(self._info['numaxes']):
                        AMC.setMove(self.device, i, False)
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
                        AMC.setMove(self.device, i, False)
                        AMC.setOutput(self.device, i, False)
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
