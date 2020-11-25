from qtpy import QtWidgets, QtCore
from pyqtgraph.widgets.SpinBox import SpinBox

from qtdptools.thread import NonstopDo, SingleDo
from qtdptools.show_utils import showMessage
from fcre.pztcontroller import OutOfRange

__all__ = ['PZTControllerUI']


class PZTControllerUI(QtWidgets.QWidget):
    """
    PZT的QWidget对象，完成PZT相应操作

    proprety:
        _systemErrorSignal-信号，系统异常时发射
        _outRangeSignal-信号，移动距离超过范围时发射
        _errorSignal-其他异常信号
        type-目标设备的类型
        name-目标设备的名称
        devpool-设备代理池
        _info-设备的信息
        _cache-缓存列表，保存当前位置

        _updateThread-循环的线程对象，更新PZT位置
        _moveThread-单次运行的线程对象，移动到目标位置
        _resetThread-单次运行的线程对象，移动到初始位置
        _doThread-单次运行的线程对象，回归偏移
        __singleMove-单次运行的线程对象列表，移动每个轴到目标位置

        ...-大量的UI项

    method:
         __init__-初始化对象，导入目标设备的类型和名称
        setupUI-所有的UI项都在此包含

        ...-大量的UI操作
    """
    _onTargetSignal = QtCore.Signal()
    _systemErrorSignal = QtCore.Signal()
    _outRangeSignal = QtCore.Signal()
    _errorSignal = QtCore.Signal(str)

    def __init__(self, name='pztcontroller', devpool=None, type='pztcontroller', numaxes=3, parent=None, **kwargs):
        super(PZTControllerUI, self).__init__(parent)
        self.name = name
        self.type = type
        self.devpool = devpool

        # 配置初始设备信息
        self._info = {'numaxes': numaxes,
                      'range': None,
                      'startPosition': None,
                      'position': None,
                      'deviation': None}
        self._info.update(kwargs)
        if not self._info['startPosition']:
            self._info['startPosition'] = self._info['numaxes'] * [0]
        self._cache = self._info['numaxes'] * [0]  # 列表，存储位置的缓存信息
        self._lastMove = self._info['numaxes'] * [0]

        # 配置线程对象
        self._updateThread = None  # 线程对象，在UI执行customInit时完成初始化
        # self._doThread = SingleDo(self._doFun)  # 线程对象，对应customDo
        self._moveThread = SingleDo(self._moveFun)  # 线程对象，对应customMove
        # 线程对象，对应customReset
        self._resetThread = SingleDo(self._resetFun)
        self._singleMoveThreads = []  # 线程对象列表，对应于单个轴customSingleMove
        for i in range(self._info['numaxes']):
            self._singleMoveThreads.append(SingleDo(self._singleMoveFun, n=i))

        # 配置UI
        self.setupUI()

        # 配置信号
        self._onTargetSignal.connect(self._moveDoneFun)
        self._systemErrorSignal.connect(self._systemErrorFun)
        self._outRangeSignal.connect(self._outRangeFun)
        self._errorSignal.connect(self._errorFun)
    
    def _moveDoneFun(self):
        self.updateInfo()
        self.positionInfoLine.setText(str(self._info['position']))
        self.deviationInfoLine.setText(str(self._info['deviation']))
        self.setButtonEnabled(True)

    def _systemErrorFun(self):
        self.devpool.do(self.type, self.name, 'close')
        if self._updateThread:
            self._updateThread.working = False
            self._updateThread.wait()
            self._updateThread = None
        showMessage('error', "{}系统异常,请排除错误重新连接.".format(self.name), QtWidgets.QMessageBox.Warning, parent=self)
        self.initButton.setEnabled(True)

    def _outRangeFun(self):
        showMessage('error', "{}超出范围,请输入正确值.".format(self.name), QtWidgets.QMessageBox.Warning, parent=self)

    def _errorFun(self, info):
        self.devpool.do(self.type, self.name, 'close')
        if self._updateThread:
            self._updateThread.working = False
            self._updateThread.wait()
            self._updateThread = None
        showMessage('error', str(info), QtWidgets.QMessageBox.Critical, parent=self)
        self.initButton.setEnabled(True)

    def initInfo(self):
        info = None
        try:
            info = self.devpool.doSafely(self.type, self.name, 'getInit')
        except Exception as e:
            self._errorSignal.emit(str(e))
        if not info:
            return
        else:
            self._info.update(info)

    def updateInfo(self):
        info = None
        try:
            info = self.devpool.doSafely(self.type, self.name, 'getInfo')
        except Exception as e:
            self._errorSignal.emit(str(e))
        if not info:
            return
        else:
            self._info.update(info)

    def setupUI(self):
        customLayout = QtWidgets.QVBoxLayout(self)

        customLayout.addWidget(QtWidgets.QLabel('type: {}, name: {}'.format(self.type, self.name)))

        buttons = QtWidgets.QWidget()
        buttonly = QtWidgets.QGridLayout(buttons)
        self.initButton = QtWidgets.QPushButton('interface')
        self.initButton.setToolTip('launch interactive interface')
        self.initButton.clicked.connect(lambda: self.customInit())
        buttonly.addWidget(self.initButton)
        self.resetButton = QtWidgets.QPushButton('reset')
        self.resetButton.setEnabled(False)
        self.resetButton.clicked.connect(lambda: self.customReset())
        buttonly.addWidget(self.resetButton)
        self.moveButton = QtWidgets.QPushButton('move')
        self.moveButton.setEnabled(False)
        self.moveButton.clicked.connect(lambda: self.customMove())
        buttonly.addWidget(self.moveButton)
        customLayout.addWidget(buttons)

        self.axis = []
        self.singleMoveButton = []
        for i in range(self._info['numaxes']):
            customLayout.addWidget(QtWidgets.QLabel('Axis {}:'.format(str(i))))
            single = QtWidgets.QWidget()
            singlely = QtWidgets.QHBoxLayout(single)
            axis = SpinBox(step=1, decimals=15)
            axis.setEnabled(False)
            axis.valueChanged.connect(lambda v, n=i: self.posChanged(v, n))
            self.axis.append(axis)
            singlely.addWidget(axis)
            button = QtWidgets.QPushButton('move')
            button.setEnabled(False)
            button.clicked.connect(lambda x, y=i: self.customSingleMove(y))
            singlely.addWidget(button)
            customLayout.addWidget(single)
            self.singleMoveButton.append(button)

        customLayout.addWidget(QtWidgets.QLabel('Range:'))
        self.rangeInfoLine = QtWidgets.QLineEdit()
        self.rangeInfoLine.setEnabled(False)
        self.rangeInfoLine.setText(str(self._info['range']))
        customLayout.addWidget(self.rangeInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('Start Point:'))
        self.startPositionInfoLine = QtWidgets.QLineEdit()
        self.startPositionInfoLine.setEnabled(False)
        self.startPositionInfoLine.setText(str(self._info['startPosition']))
        customLayout.addWidget(self.startPositionInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('Position:'))
        self.positionInfoLine = QtWidgets.QLineEdit()
        self.positionInfoLine.setEnabled(False)
        self.positionInfoLine.setText(str(self._info['position']))
        customLayout.addWidget(self.positionInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('Deviation:'))
        self.deviationInfoLine = QtWidgets.QLineEdit()
        self.deviationInfoLine.setEnabled(False)
        self.deviationInfoLine.setText(str(self._info['deviation']))
        customLayout.addWidget(self.deviationInfoLine)

    def setButtonEnabled(self, set):
        self.moveButton.setEnabled(set)
        self.resetButton.setEnabled(set)
        for i in range(self._info['numaxes']):
            self.singleMoveButton[i].setEnabled(set)

    def posChanged(self, pos, n):
        self._cache[n] = pos

    def _singleMoveFun(self, n):
        try:
            self._lastMove[n] = self._cache[n]
            self.devpool.doSafely(self.type, self.name, 'move', tuple(self._lastMove))
        except OutOfRange:
            self._outRangeSignal.emit()
        except SystemError:
            self._systemErrorSignal.emit()
        except Exception as e:
            self._errorSignal.emit(str(e))
        finally:
            self._onTargetSignal.emit()

    def customSingleMove(self, n):
        self.setButtonEnabled(False)
        self._singleMoveThreads[n].start()
        
    def _moveFun(self):
        try:
            for i in range(self._info['numaxes']):
                self._lastMove[i] = self._cache[i]
            self.devpool.doSafely(self.type, self.name, 'move', tuple(self._lastMove))
        except OutOfRange:
            self._outRangeSignal.emit()
        except SystemError:
            self._systemErrorSignal.emit()
        except Exception as e:
            self._errorSignal.emit(str(e))
        finally:
            self._onTargetSignal.emit()

    def customMove(self):
        self.setButtonEnabled(False)
        self._moveThread.start()

    def customInit(self):
        self.initButton.setEnabled(False)
        if not self.devpool.do(self.type, self.name, 'isOpen'):
            showMessage('error', 'device is not open! Please reconnect', 
                    QtWidgets.QMessageBox.Warning, parent=self)
            self.initButton.setEnabled(True)
            return
        self.setButtonEnabled(True)
        if not self._updateThread:
            self._updateThread = NonstopDo(self._updateFun)
            self._updateThread.start(QtCore.QThread.LowPriority)
        else:
            pass
        self.initInfo()
        for i in range(self._info['numaxes']):
            self.axis[i].setValue(float(self._info['startPosition'][i]))
            self.axis[i].setEnabled(True)
            self._lastMove[i] = float(self._info['startPosition'][i])
        self.rangeInfoLine.setText(str(self._info['range']))
        self.startPositionInfoLine.setText(str(self._info['startPosition']))

    def _updateFun(self):
        self.updateInfo()
        self.positionInfoLine.setText(str(self._info['position']))
        self.deviationInfoLine.setText(str(self._info['deviation']))

    def customReset(self):
        self.setButtonEnabled(False)
        self.initInfo()
        for i in range(self._info['numaxes']):
            self.axis[i].setValue(float(self._info['startPosition'][i]))
            self._lastMove[i] = float(self._info['startPosition'][i])
        self._resetThread.start()

    def _resetFun(self):
        try:
            self.devpool.doSafely(self.type, self.name, 'reset')
        except OutOfRange:
            self._outRangeSignal.emit()
        except SystemError:
            self._systemErrorSignal.emit()
        except Exception as e:
            self._errorSignal.emit(str(e))
        finally:
            self._onTargetSignal.emit()

    def closeEvent(self, ev):
        if self._updateThread and self._updateThread.isRunning():
            self._updateThread.working = False
            self._updateThread.wait()
        if self._moveThread and self._moveThread.isRunning():
            self._moveThread.wait()
        if self._resetThread and self._resetThread.isRunning():
            self._resetThread.wait()
        for single in self._singleMoveThreads:
            if single and single.isRunning():
                single.wait()
        ev.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    from pyqtgraph.dockarea import DockArea, Dock
    from fcre.pool import DevPool

    pztui = PZTControllerUI('pzt', DevPool(), 'pilong', **{'numaxes': 2})
    # pztui.customInit()
    
    d = DockArea()
    win.setCentralWidget(d)
    dock = Dock('pilong')
    dock.addWidget(pztui)
    d.addDock(dock)
    win.show()
    app.exec_()
