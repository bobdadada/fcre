import os
import time

from PIL import Image

import numpy as np
import cv2 as cv

from qtpy import QtWidgets, QtCore
import pyqtgraph as pg

from qtdptools.show_utils import showMessage

__all__ = ['CameraUI']


class CameraUI(QtWidgets.QWidget):
    """
    相机的QWidget对象，完成相机的读取操作

    proprety:
        _readErrorSignal-信号，但读取相机图像失败时激活
        type-目标设备的类型
        name-目标设备的名称
        devpool-设备代理池
        _catchTimer-定时器，由于更新图像
        _catchTimePoint-完成图像操作的时间点，用于计算fps

        ...-大量的UI项

    method:
         __init__-初始化对象，导入目标设备的类型和名称
        setupUI-所有的UI项都在此包含

        ...-大量的UI操作
    """

    _readErrorSignal = QtCore.Signal(str)

    def __init__(self, name='camera', devpool=None, type='camera', relaxtime=100, parent=None, **kwargs):
        super(CameraUI, self).__init__(parent)
        self.type = type
        self.name = name
        self.devpool = devpool

        if not relaxtime:
            relaxtime = 100
        self.relaxtime = relaxtime

        # 配置线程对象
        self._catchTimer = QtCore.QTimer()  # 定时器，用于更新图像
        self._catchTimer.timeout.connect(self._updateFun)
        self._catchTimePoint = 0  # 拍摄时间点，用于计算fps

        # 配置UI
        self.setupUI()

        # 配置信号
        self._readErrorSignal.connect(self._readErrorFun)

    def setupUI(self):
        customLayout = QtWidgets.QVBoxLayout(self)

        customLayout.addWidget(QtWidgets.QLabel('type: {}, name: {}'.format(self.type, self.name)))

        buttons = QtWidgets.QWidget()
        buttonly = QtWidgets.QHBoxLayout(buttons)
        self._startButton = QtWidgets.QPushButton('start')
        self._startButton.clicked.connect(self.customStart)
        buttonly.addWidget(self._startButton)
        self._saveButton = QtWidgets.QPushButton('save')
        self._saveButton.clicked.connect(self.customSave)
        buttonly.addWidget(self._saveButton)

        customLayout.addWidget(buttons)

        self._stateLabel = QtWidgets.QLabel('fps: , image shape: ')
        customLayout.addWidget(self._stateLabel)

        graph = pg.GraphicsLayoutWidget()
        self._viewbox = pg.ViewBox(enableMouse=False)
        self._viewbox.setRange(QtCore.QRectF(0, 0, 600, 600))
        graph.setCentralItem(self._viewbox)
        self._currImg = None
        self._imgItem = pg.ImageItem()
        self._viewbox.addItem(self._imgItem)
        customLayout.addWidget(graph)

    def viewBox(self):
        return self._viewbox

    def addItem(self, item, ignoreBounds=False):
        self._viewbox.addItem(item, ignoreBounds=ignoreBounds)

    def _readErrorFun(self, name):
        showMessage('error', "can't read image from camera {}!".format(name), QtWidgets.QMessageBox.Warning, parent=self)

    def customSave(self):
        if not isinstance(self._currImg, np.ndarray):
            showMessage('error', "camera not open", QtWidgets.QMessageBox.Warning, parent=self)
            return
        self.customStop()
        filename, ok = QtWidgets.QFileDialog.getSaveFileName(self, 'save points to file', os.getcwd(), '*.jpg,*.tiff')
        if ok:
            im = Image.fromarray(self._currImg)
            im.save(filename)

    def customStart(self):
        self._startButton.setEnabled(False)
        self._startButton.setText('stop')
        try:
            self._startButton.clicked.disconnect(self.customStart)
        except:
            pass
        try:
            self._startButton.clicked.disconnect(self.customStop)
        except:
            pass
        finally:
            self._startButton.clicked.connect(self.customStop)
        self._catchTimePoint = time.time()
        self._catchTimer.start(self.relaxtime)
        self._startButton.setEnabled(True)

    def customStop(self):
        self._startButton.setEnabled(False)
        if self._catchTimer.isActive():
            self._catchTimer.stop()
        self._startButton.setText('start')
        try:
            self._startButton.clicked.disconnect(self.customStop)
        except:
            pass
        try:
            self._startButton.clicked.disconnect(self.customStart)
        except:
            pass
        finally:
            self._startButton.clicked.connect(self.customStart)
        self._startButton.setEnabled(True)

    def _updateFun(self):
        img = None
        try:
            img = self.devpool.do(self.type, self.name, 'read')
        except Exception:
            pass
        if not isinstance(img, np.ndarray):
            self.customStop()
            self._readErrorSignal.emit(self.name)
            return
        if len(img.shape) == 2:
            pass
        elif len(img.shape) == 3:
            img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            if len(img.shape) == 3:
                img = img[:, :, 0]
        self._currImg = img
        self._imgItem.setImage(img.T)
        self._imgItem.setRect(QtCore.QRect(0, 0, 600, 600))
        interval = time.time() - self._catchTimePoint
        self._catchTimePoint = time.time()
        self._stateLabel.setText('fps: {} image shape: {}'.format(int(1 / interval), str(img.shape)))

    def customReset(self):
        pass

    def getCurrentImage(self):
        return self._currImg

    def closeEvent(self, ev):
        if self._catchTimer:
            self._catchTimer.stop()
        ev.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    from pyqtgraph.dockarea import DockArea, Dock
    from fcre.pool import DevPool
    from fcre.camera import Camera

    devpool = DevPool()

    devpool.register('camera', 'cm')
    devpool.do('camera', 'cm', 'connect', 0)
    d = DockArea()
    win.setCentralWidget(d)
    dock = Dock('cm')
    UI = CameraUI('camera', devpool, 'cm')
    dock.addWidget(UI)
    d.addDock(dock)
    win.show()
    app.exec_()
