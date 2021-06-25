# -*- coding: utf-8 -*-

__all__ = ['SCShutter']

import serial
import threading
from bidict import bidict

class SCShutter(object):
    """
    光快门本地对象，可以控制Thorlab公司的SC10，以串口传递串行数据的方式连接设备。

    proprety:
        _info-保持设备信息
        _modeNameTable-设备功能对应的模式表
        _terminator-串口终止符
        _start_character-串口下一条语句起始符

        device-目标设备对象
        name-目标设备对象的本地名称


    method:
        __init__-初始化
        _write-写命令
        _quiry-询问设备

        connect-以串口的方式连接设备
        init-初始化
        getInfo-返回信息
        getAllInfo-返回信息
        setAllInfo-设置信息
        getModeNameTable-返回模式表信息
        getModeName-获得模式名称
        setModeName-以名称方式设置模式
        isOpen-判断设备是否打开
        disable-关闭光快门
        enable-打开光快门
        isEnable-判断设备是否使能
        setOpenDuration-设置打开时间
        getOpenDuration-获得打开时间
        setShutDuration-设置关闭时间
        getShutDuration-获得关闭时间
        setRepeatCount-设置重复次数
        getRepeatCount-获得重复次数
        close-关闭物理设备
    """

    _modeNameTable = bidict({
        'Manual': 1,
        'Auto': 2,
        'Single': 3,
        'Repeat': 4,
        'External Gate': 5
    })
    _start_character = b'> '
    _terminator = b'\r'

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.device = None
        self._info ={'enable': False,
                     'shuttime': None,
                     'opentime': None,
                     'mode': None,
                     'modename':None,
                     'count':None}
        self._lock = threading.RLock()

    def isOpen(self):
        with self._lock:
            if not self.device:
                return False
            else:
                return True

    def _write(self, command):
        with self._lock:
            if not self.device:
                return
            command = command.encode()
            size = self.device.write(command+self._terminator)
            self.device.read_until(self._start_character)
            return size

    def _quiry(self, command):
        with self._lock:
            if not self.device:
                return
            command = (command + '?').encode()
            self.device.write(command+self._terminator)
            ret = self.device.read_until(self._terminator)
            if ret == command+self._terminator:
                ret = self.device.read_until(self._terminator).replace(self._terminator, b'')
                self.device.read_until(self._start_character)
                return ret.decode()
            else:
                self.device.read_until(self._start_character)
                return ''

    def connect(self, port, baudrate, timeout=None, *args, **kwargs):
        with self._lock:
            if self.device:
                return
            self.device = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            self.init()

    def init(self):
        with self._lock:
            self.isEnable()
            self.getOpenDuration()
            self.getShutDuration()
            self.getMode()
            self.getRepeatCount()

    def getModeNameTable(self):
        return dict(self._modeNameTable)

    def getModeName(self):
        with self._lock:
            mode = self.getMode()
            if mode:
                self._info['modename'] = self._modeNameTable.inverse[mode]
            return self._info['modename']

    def setModeName(self, name):
        with self._lock:
            if not self.device:
                return
            self.setMode(self._modeNameTable[name])

    def getInfo(self):
        with self._lock:
            return {'enable': self.isEnable(),
                     'shuttime': self.getShutDuration(),
                     'opentime': self.getOpenDuration(),
                     'modename':self.getModeName(),
                     'count':self.getRepeatCount()}

    def getAllInfo(self):
        with self._lock:
            return self.getInfo()

    def setAllInfo(self, info):
        with self._lock:
            info.pop('enable', None)
            self._info.update(info)
            self.setOpenDuration(self._info['opentime'])
            self.setShutDuration(self._info['shuttime'])

    def disable(self):
        with self._lock:
            if not self.device:
                return
            if not self.isEnable():
                return
            else:
                self._info['enable'] = not self._info['enable']
                self._write('ens')

    def enable(self):
        with self._lock:
            if not self.device:
                return
            if self.isEnable():
                return
            else:
                self._info['enable'] = not self._info['enable']
                self._write('ens')

    def isEnable(self):
        with self._lock:
            if not self.device:
                return
            ret = self._quiry('ens')
            self._info['enable'] = bool(int(ret))
            return self._info['enable']

    def setMode(self, n):
        """
        Set operating mode
        Where n equals an associated mode—
        mode=1: Sets the unit to Manual Mode
        mode=2: Sets the unit to Auto Mode
        mode=3: Sets the unit to Single Mode
        mode=4: Sets the unit to Repeat Mode
        mode=5: Sets the unit to the External Gate Mode
        :param n: number
        :return:
        """
        with self._lock:
            if not self.device:
                return
            self.disable()
            self._info['mode'] = n
            self._write('mode=%d'%n)

    def getMode(self):
        with self._lock:
            if not self.device:
                return
            ret = self._quiry('mode')
            self._info['mode'] = int(ret)
            return self._info['mode']
        
    def setOpenDuration(self, ms):
        with self._lock:
            if not self.device:
                return
            ms = int(ms)
            if ms > 99999:
                raise ValueError('Duration time longer than 99999')
            self._info['opentime'] = ms
            self._write('open=%d'%ms)

    def getOpenDuration(self):
        with self._lock:
            if not self.device:
                return
            ret = self._quiry('open')
            self._info['opentime'] = int(ret)
            return self._info['opentime']
    
    def setShutDuration(self, ms):
        with self._lock:
            if not self.device:
                return
            ms = int(ms)
            if ms > 99999:
                raise ValueError('Duration time longer than 99999')
            self._info['shuttime'] = ms
            self._write('shut=%d'%ms)

    def getShutDuration(self):
        with self._lock:
            if not self.device:
                return
            ret = self._quiry('shut')
            self._info['shuttime'] = int(ret)
            return self._info['shuttime']
    
    def setRepeatCount(self, n):
        with self._lock:
            if not self.device:
                return
            n = int(n)
            if n > 99 or n < 1:
                raise ValueError('number of repeat count must be from 1 to 99')
            self._info['count'] = n
            self._write('rep=%d'%n)
    
    def getRepeatCount(self):
        with self._lock:
            if not self.device:
                return
            ret = self._quiry('rep')
            self._info['count'] = int(ret)
            return self._info['count']

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
        print('关闭光快门:{}'.format(self.name))
        self.close()
