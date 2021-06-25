from qtpy import QtWidgets, QtCore
import pyqtgraph as pg

from qtdptools.thread import NonstopDo
from qtdptools.show_utils import showQuickMessage
from qtdptools.utils import validateRet

__all__ = ['ShutterUI']


class ShutterUI(QtWidgets.QWidget):
    """
    光快门的QWidget对象，完成光快门的操作

    proprety:
        type-目标设备的类型
        name-目标设备的名称
        devpool-设备代理池
        _info-设备的信息

        _updateThread-循环的线程对象，更新PZT位置

        ...-大量的UI项

    method:
        __init__-初始化对象，导入目标设备的类型和名称
        setupUI-所有的UI项都在此包含

        ...-大量的UI操作
    """

    def __init__(self, name='shutter', devpool=None, type='shutter', parent=None, *args, **kwargs):
        super(ShutterUI, self).__init__(parent)
        self.name = name
        self.type = type
        self.devpool = devpool

        # 配置初始设备信息
        self._info = {}
        self._info.update(kwargs)

        # 配置线程对象
        self._updateThread = None  # 线程对象，在UI执行customInit时完成初始化

        # 配置UI
        self.setupUI()

    def setupUI(self):
        customLayout = QtWidgets.QVBoxLayout(self)

        customLayout.addWidget(QtWidgets.QLabel(
            'type: {}, name: {}'.format(self.type, self.name)))

        buttons = QtWidgets.QWidget()
        buttonly = QtWidgets.QHBoxLayout(buttons)
        self.initButton = QtWidgets.QPushButton('interface')
        self.initButton.setToolTip('launch interactive interface')
        self.initButton.clicked.connect(lambda: self.customInit())
        buttonly.addWidget(self.initButton)
        self.setButton = QtWidgets.QPushButton('set')
        self.setButton.clicked.connect(lambda: self.customSet())
        self.setButton.setEnabled(False)
        buttonly.addWidget(self.setButton)
        self.enableCheck = QtWidgets.QCheckBox('enable')
        self.enableCheck.clicked[bool].connect(lambda x: self.customEnable(x))
        buttonly.addWidget(self.enableCheck)
        customLayout.addWidget(buttons)

        customLayout.addWidget(QtWidgets.QLabel('Mode:'))
        self.modeComboBox = pg.ComboBox()
        customLayout.addWidget(self.modeComboBox)

        customLayout.addWidget(QtWidgets.QLabel('OpenDuration(ms):'))
        self.opentimeSpinbox = pg.SpinBox(value=20, bounds=(1, None), step=1)
        customLayout.addWidget(self.opentimeSpinbox)

        customLayout.addWidget(QtWidgets.QLabel('ShutDuration(ms):'))
        self.shuttimeSpinbox = pg.SpinBox(value=200, bounds=(1, None), step=1)
        customLayout.addWidget(self.shuttimeSpinbox)

        customLayout.addWidget(QtWidgets.QLabel('RepeatCount:'))
        self.countSpinbox = pg.SpinBox(value=1, bounds=(1, None), step=1)
        customLayout.addWidget(self.countSpinbox)

        customLayout.addWidget(QtWidgets.QLabel('Mode Info:'))
        self.modeInfoLine = QtWidgets.QLineEdit('None')
        self.modeInfoLine.setEnabled(False)
        customLayout.addWidget(self.modeInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('Enable Info:'))
        self.enableInfoLine = QtWidgets.QLineEdit('False')
        self.enableInfoLine.setEnabled(False)
        customLayout.addWidget(self.enableInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('OpenDuration Info(ms):'))
        self.opentimeInfoLine = QtWidgets.QLineEdit('None')
        self.opentimeInfoLine.setEnabled(False)
        customLayout.addWidget(self.opentimeInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('ShutDuration Info(ms):'))
        self.shuttimeInfoLine = QtWidgets.QLineEdit('None')
        self.shuttimeInfoLine.setEnabled(False)
        customLayout.addWidget(self.shuttimeInfoLine)

        customLayout.addWidget(QtWidgets.QLabel('RepeatCount Info:'))
        self.countInfoLine = QtWidgets.QLineEdit('None')
        self.countInfoLine.setEnabled(False)
        customLayout.addWidget(self.countInfoLine)

    def customSet(self):
        try:
            mode = int(self.modeComboBox.value())
            self.devpool.doSafely(self.type, self.name, 'setMode', mode)
            opentime = float(self.opentimeSpinbox.value())
            self.devpool.doSafely(self.type, self.name,
                                  'setOpenDuration', opentime)
            shuttime = float(self.shuttimeSpinbox.value())
            self.devpool.doSafely(self.type, self.name,
                                  'setShutDuration', shuttime)
        except Exception as e:
            self._updateThread = None
            self.devpool.do(self.type, self.name, 'close')
            self.initButton.setEnabled(True)
            showQuickMessage(5000, 'Error', str(
                e), QtWidgets.QMessageBox.Critical, parent=self)

    def customEnable(self, x):
        try:
            if x:
                self.devpool.doSafely(self.type, self.name, 'enable')
            else:
                self.devpool.doSafely(self.type, self.name, 'disable')
        except Exception as e:
            self.devpool.do(self.type, self.name, 'close')
            self.initButton.setEnabled(True)
            showQuickMessage(5000, 'Error', str(
                e), QtWidgets.QMessageBox.Critical, parent=self)

    def updateInfo(self):
        info = self.devpool.do(self.type, self.name, 'getInfo')
        if not info:
            return
        else:
            self._info.update(info)

    def customInit(self):
        self.initButton.setEnabled(False)
        if not self.devpool.do(self.type, self.name, 'isOpen'):
            showQuickMessage(5000, 'NotOpen', 'device is not open! Please reconnect',
                             QtWidgets.QMessageBox.Warning, parent=self)
            self.initButton.setEnabled(True)
            return
        try:
            self.modeComboBox.setItems(validateRet(self.devpool.doSafely(self.type, self.name, 'getModeNameTable'),
                                                   '无法获取光快门模式表', dict))
            self.modeComboBox.setCurrentIndex(self.modeComboBox.findText(
                self.devpool.doSafely(self.type, self.name, 'getModeName')))
            self.opentimeSpinbox.setValue(self.devpool.doSafely(
                self.type, self.name, 'getOpenDuration'))
            self.shuttimeSpinbox.setValue(self.devpool.doSafely(
                self.type, self.name, 'getShutDuration'))
            self.countSpinbox.setValue(self.devpool.doSafely(
                self.type, self.name, 'getRepeatCount'))
        except:
            self.initButton.setEnabled(True)
            return
        self.setButton.setEnabled(True)
        if not self._updateThread:
            self._updateThread = NonstopDo(self._updateFun, 200)
            self._updateThread.start(QtCore.QThread.LowPriority)
        else:
            pass

    def _updateFun(self):
        self.updateInfo()
        self.modeInfoLine.setText(str(self._info['modename']))
        self.opentimeInfoLine.setText(str(self._info['opentime']))
        self.shuttimeInfoLine.setText(str(self._info['shuttime']))
        self.enableInfoLine.setText(str(self._info['enable']))
        self.countInfoLine.setText(str(self._info['count']))

    def customReset(self):
        pass

    def closeEvent(self, ev):
        if self._updateThread and self._updateThread.isRunning:
            self._updateThread.delSafely()
        ev.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    from pyqtgraph.dockarea import DockArea, Dock
    from fcre.pool import DevPool
    devpool = DevPool()
    devpool.register('shutter', 'scsht')
    d = DockArea()
    win.setCentralWidget(d)
    dock = Dock('scsht')
    dock.addWidget(ShutterUI('shutter', devpool, 'scsht'))
    d.addDock(dock)
    win.show()
    app.exec_()
