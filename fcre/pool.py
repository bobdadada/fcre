# -*- coding:utf-8 -*-
"""
This file create a pool to storage the devices
"""

__all__ = ['DevPool', 'Constant', 'delete']

import sys
import threading
import os
from datetime import datetime
import json
import importlib
import importlib.util

class DevPoolError(Exception):
    """
    设备池根异常
    """

class NoDevError(DevPoolError):
    """
    设备不在设备池中
    """

class DevMethodNotImplementedError(DevPoolError):
    """
    设备方法获取失败
    """

# 将打印结果都保存到文件中
def _decorator_write_to_file(file):
    def wrap(_print):
        def _rprint(*args, **kwargs):
            try:
                try:
                    return _print(*args, file=file, **kwargs)
                except ValueError:  # 可能file的I/O已经关闭
                    return _print(*args, file=sys.stdout, **kwargs)
            except Exception:
                pass
        return _rprint
    return wrap


# 用于检查对象是否有write()方法
def _validate_file_object(file):
    if not hasattr(file, 'write'):
        return False
    return True

# 所有类型对象
deviceObjects = {
    'pztcontroller': {'amc': 'AMCPZTController', 'pi': 'PIPZTController'},
    'camera': 'Camera',
    'shutter': {'sc': 'SCShutter'}
}
deviceKeys = ('amc', 'pi', 'sc')

def _getObjectName(_type, _name):
    t0 = deviceObjects[_type]
    if isinstance(t0, dict):
        for key in deviceKeys:
            if _name.lower().startswith(key):
                return t0[key]
    elif isinstance(t0, str):
        return t0

# DevPool manage all register device
class DevPool(object):
    """
    设备池，用于连接设备。保存了所有需要连接的对象。

    proprety:
        _instance-类属性，实际上是由类对象所创建的实例对象
        _instance_lock-类属性，线程锁，保证安全建立DevPool单例
        _devices-字典，以设备类型保存子集合，每个集合元素都是设备对象，更新_devices需要加锁。
        _devicesnames-字典，以设备类型保存子set，每个集合元素都是设备对象的名称
        _print-修饰过后的print函数

    method:
        __new__-创建单例结构的设备池
        __init__-初始化
        setFile-设置print函数打印到目标文件中，默认情况为stdout
        getRegistered-获取所有已经注册的设备名称
        register-以命名参数的方式注册设备对象
        _getDevice-以类型查找的方式获得目标设备
        doSafely-安全地运行设备对象具体方法
        do-运行目标设备对象具体方法
        unregister-移除某个特定设备，为了节省对象创建所需的时间，我们许哟目标设备存在本地映射1，并且具有close()方法
        unregisterAll-全部移除
        delete-删除单例
    """

    _instance = None
    _instance_lock = threading.RLock()

    def __new__(cls, *args, file=sys.stdout, **kwargs):
        if not DevPool._instance:
            with DevPool._instance_lock:
                DevPool._instance = super(DevPool, cls).__new__(cls)
                DevPool._instance.setFile(file)
                DevPool._instance._print('{}: Create a DevPool singleton'.format(datetime.now()))
        else:
            print('DevPool is existent. Ignore any input argument')
        return  DevPool._instance

    def __init__(self, *args, **kwargs):
        with DevPool._instance_lock:
            self._devices = {}
            self._devicesnames = {}

    def setFile(self, f):
        if _validate_file_object(f):
            self._print = _decorator_write_to_file(f)(print)
        else:
            print("file object has no attribute 'write', print to stdout")
            self._print = print

    def register(self, type, name, *args, **kwargs):
        """
        注册设备时候，为了安全起见，我们给它加锁。保证多线程安全。
        :param type: 设备类型。
        :param name: '设备名称。
        :return: 返回所有注册设备的字典，字典的键为type名称，值为所有同类型设备的名称集合。
        """
        _type = type
        _name = name
        
        try:
            _type_module = importlib.import_module('fcre.'+_type)
        except ImportError as e:
            print(e)
            return
        
        """
        if os.path.isfile(os.path.join(os.path.dirname(__file__), _type.lower() + '.pyd')):
            spec = importlib.util.spec_from_file_location(_type, os.path.join(os.path.dirname(__file__), _type.lower() + '.pyd'))
            _type_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_type_module)
        else:
            spec = importlib.util.spec_from_file_location(_type, os.path.join(os.path.dirname(__file__), _type.lower() + '.py'))
            _type_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_type_module)
        """
        
        _type_object_name = _getObjectName(_type, _name)
        _type_object = getattr(_type_module, _type_object_name)

        with DevPool._instance_lock:
            if _type not in self._devices:
                self._devices[_type] = set()
                self._devicesnames[_type] = set()
                self._devices[_type].add(_type_object(_name))
                self._devicesnames[_type].add(_name)
                self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), _type, _name))
            else:
                if _name in self._devicesnames[_type]:
                    self._print('{}: already register Device type:{}, name:{}'.format(datetime.now(), _type, _name))
                else:
                    self._devices[_type].add(_type_object(_name))
                    self._devicesnames[_type].add(_name)
                    self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), _type, _name))

        # with DevPool._instance_lock:
        #     for key in kwargs.keys():
        #         if key not in self._devices:
        #             self._devices[key] = set()
        #             self._devicesnames[key] = set()
        #             if isinstance(kwargs[key], (list, tuple)):
        #                 for item in kwargs[key]:
        #                     self._devices[key].add(item)
        #                     self._devicesnames[key].add(item.name)
        #                     self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), key, item.name))
        #             else:
        #                 self._devices[key].add(kwargs[key])
        #                 self._devicesnames[key].add(kwargs[key].name)
        #                 self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), key, kwargs[key].name))
        #         else:
        #             if isinstance(kwargs[key], (list, tuple)):
        #                 for item in kwargs[key]:
        #                     if item.name in self._devicesnames[key]:
        #                         self._print('{}: already register Device type:{}, name:{}'.format(datetime.now(), key, item.name))
        #                         continue
        #                     self._devices[key].add(item)
        #                     self._devicesnames[key].add(item.name)
        #                     self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), key, item.name))
        #             else:
        #                 if kwargs[key].name in self._devicesnames[key]:
        #                     self._print('{}: already register Device type:{}, name:{}'.format(datetime.now(), key, kwargs[key].name))
        #                 else:
        #                     self._devices[key].add(kwargs[key])
        #                     self._devicesnames[key].add(kwargs[key].name)
        #                     self._print('{}: register Device type:{}, name:{}'.format(datetime.now(), key, kwargs[key].name))

        return self.getRegistered()

    def getRegistered(self):
        return self._devicesnames

    def _getDevice(self, type, name):
        if type in self._devices:
            for dev in self._devices[type]:
                if name == dev.name:
                    return dev
        else:
            return

    # 安全地运行特定对象的方法，当发生某种错误时，弹出相应地异常。
    def doSafely(self, type, name, attr, *args, **kwargs):
        dev = self._getDevice(type, name)
        if not dev:
            self._print('{}: Get device failed'.format(datetime.now()))
            raise NoDevError('{}: {} not in this Devpool'.format(type, name))
        # self._print('{}: Get device successfully device:{}'.format(datetime.now(), str(dev)))  # 成功的操作都应该在物理上显示
        try:
            method = getattr(dev, attr)
        except Exception as e:
            self._print('{}: Get method:{} failed'.format(datetime.now(), attr))
            self._print('{}: {}'.format(datetime.now(), str(e)))
            raise DevMethodNotImplementedError(str(e))
        # self._print('{}: Get method: {} successfully'.format(datetime.now(), attr))  # 成功的操作都应该在物理上显示
        try:
            return method(*args, **kwargs)
        except Exception as e:
            self._print('{}: Run method:{} failed'.format(datetime.now(), attr))
            self._print('{}: {}'.format(datetime.now(), str(e)))
            raise
    
    def do(self, type, name, attr, *args, **kwargs):
        dev = self._getDevice(type, name)
        if not dev:
            self._print('{}: Get device failed'.format(datetime.now()))
            return
        try:
            method = getattr(dev, attr)
        except Exception as e:
            self._print('{}: Get method:{} failed'.format(datetime.now(), attr))
            self._print('{}: {}'.format(datetime.now(), str(e)))
            return
        # self._print('{}: Get method: {} successfully'.format(datetime.now(), attr))  # 成功的操作都应该在物理上显示
        try:
            return method(*args, **kwargs)
        except Exception as e:
            self._print('{}: Run method:{} failed'.format(datetime.now(), attr))
            self._print('{}: {}'.format(datetime.now(), str(e)))
            return

    def unregister(self, type, name):
        target = None
        if type in self._devices:
            for dev in self._devices[type]:
                if name == dev.name:
                    target = dev
                    break
        if not target:
            self._print('{}: No Device type:{}, name:{}'.format(datetime.now(), type, name))
            return
        target.close()
        self._print('{}: Unregister Device type:{}, name:{}'.format(datetime.now(), type, name))


    def unregisterAll(self):
        for type in self._devices:
            devs = self._devices[type]
            for dev in devs:
                dev.close()
                self._print('{}: Unregister Device type:{}, name:{}'.format(datetime.now(), type, dev.name))

    def delete(self):
        DevPool._instance = None
        self.__del__()

    def __del__(self):
        self.unregisterAll()
        print('Delete DevPool')

def delete(obj):
    if hasattr(obj, 'delete'):
        obj.delete()
    else:
        pass

class SubThreadsPool(object):
    """
    子线程线程池，用于存储线程对象，子线程对象需要有isFinised()->bool，exit()->None方法

    property:
        _subthreads-集合对象set，用于存储线程
    
    method:
        add-添加线程对象
        remove-等待线程完成，并移除线程对象
        removeAll-等待池中所有对象都完成，并全部移除
    """

    def __init__(self):
        self._subthreads = set([])

    def add(self, thread):
        self._subthreads.add(thread)
    
    def remove(self, thread):
        if not thread.isFinished():
            thread.exit()
        self._subthreads.remove(thread)
    
    def removeAll(self):
        for t in self._subthreads:
            t.exit()
        self._subthreads.clear()
    
    def __del__(self):
        self.removeAll()

# Save the important constants in the experiment.
class Constant(object):
    """
    配置参数的类，保存了所有参数信息。

    proprety:
        _config-以字典套字典的形式保存参数，不过只有两重。

    method:
        __init__-初始化
        set-设置某个section下的key:value参数
        get-获得某个section下key对应的参数
        getAll-获得所有参数的拷贝
        read-从文件中导入json
        write-以json的方式将配置参数写目标入文件中
    """

    def __init__(self):
        self._config = {}
        self._lock = threading.RLock()

    def set(self, section, key, value):
        with self._lock:
            if section not in self._config:
                self._config[section] = {}
            self._config[section].update({key: value})

    def setSection(self, section, item):
        with self._lock:
            if section not in self._config:
                self._config[section] = {}
            self._config[section].update(item)

    def get(self, section, key):
        with self._lock:
            try:
                return self._config[section][key]
            except KeyError:
                return

    def getSection(self, section):
        with self._lock:
            try:
                return self._config[section].copy()
            except KeyError:
                return

    def getAll(self):
        with self._lock:
            return self._config.copy()

    def read(self, fp):
        if not fp:
            return
        else:
            with self._lock:
                self._config.update(json.load(fp))

    def write(self, fp=None):
        with self._lock:
            if not fp:
                with open(os.path.join(os.getcwd(), 'constant.json'), 'w', encoding='utf-8') as fp:
                    json.dump(self._config, fp, ensure_ascii=False, indent=2)
            elif isinstance(fp, str):
                with open(fp, 'w', encoding='utf-8') as fp:
                    json.dump(self._config, fp, ensure_ascii=False, indent=2)
            elif hasattr(fp, 'write'):
                json.dump(self._config, fp, ensure_ascii=False, indent=2)

# 配置文件类，用于简单的键值对配对
class Config(object):
    """
    导入JSON文件到类属性的方法配置参数，与Constant类相比较为简单。

    proprety:
        *-单层JSON文件导入的属性

    method:
        __init__-初始化
        dump-将修改后的参数保存到文件中
    """
    _lock = threading.RLock()

    def __init__(self, filename):
        self._filename = filename

        with open(filename, encoding='utf-8') as fp:
            self.__dict__.update(json.load(fp))

    def dump(self, filename=None):
        with Config._lock:
            if filename is None:
                filename = self._filename
            data = {}
            for key in self.__dict__:
                if not key.startswith('_'):
                    data[key] = self.__dict__[key]
            with open(filename, 'w', encoding='utf-8') as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)

    def __getattr__(self, attr):
        with Config._lock:
            try:
                return self.__dict__[attr]
            except:
                return None
    
    def __setattr__(self, attr, value):
        with Config._lock:
            self.__dict__[attr] = value
