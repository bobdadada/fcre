# -*- coding: utf-8 -*-

__all__ = ['Camera',  'Pretreatment', 'Evaluation', 'showMultiplyCameras', 'openCameras', 'readImages']

import numpy as np
import threading
import cv2 as cv
import time
import os


class NotOpenError(Exception):
    pass


class ReadFailedError(Exception):
    pass


class Camera(object):
    """
    定义Camera类，负责实现图片的拍摄被记录

    property:
        name-名称
        cap-相机实体
        properties-相机的属性
        _lock-锁，保证多线程安全
        _readState-读取状态
        _lastImg-图像，保存最新图像

    method:
        __init__-创建相机本地映射
        isOpen-判断相机是否连接
        isReading-判断相机是否正在读取
        connect-连接相机
        init-导入相机参数
        set-设置参数
        read-读取图像
        getLastImage-获取最新值
        close-释放相机
        __del__-防止没有移除
    """

    def __init__(self, name, *args, **kwargs):
        # 导入一个相机
        self.name = name
        self._lock = threading.RLock()
        self.cap = None

    def isOpen(self):
        with self._lock:
            if not self.cap:
                return False
            else:
                return True

    def connect(self, id, cvbackend=0, *args, **kwargs):
        with self._lock:
            if self.cap:
                return
            self.cap = cv.VideoCapture(id + cvbackend)
            if not self.cap.isOpened:
                raise NotOpenError('No camera named {}'.format(id))
            # 获取相机信息
            self.properties = {}
            self._lastImg = None
            self._readState = False
            self.init()

    def init(self):
        with self._lock:
            if not self.cap:
                return
            self.properties["width"] = [self.cap.get(cv.CAP_PROP_FRAME_WIDTH), cv.CAP_PROP_FRAME_WIDTH]
            self.properties["height"] = [self.cap.get(cv.CAP_PROP_FRAME_HEIGHT), cv.CAP_PROP_FRAME_HEIGHT]
            self.properties["frameRate"] = [self.cap.get(cv.CAP_PROP_FPS), cv.CAP_PROP_FPS]
            self.properties["brightness"] = [self.cap.get(cv.CAP_PROP_BRIGHTNESS), cv.CAP_PROP_BRIGHTNESS]
            self.properties["contrast"] = [self.cap.get(cv.CAP_PROP_CONTRAST), cv.CAP_PROP_CONTRAST]
            self.properties["saturation"] = [self.cap.get(cv.CAP_PROP_SATURATION), cv.CAP_PROP_SATURATION]
            self.properties["hue"] = [self.cap.get(cv.CAP_PROP_HUE), cv.CAP_PROP_HUE]
            self.properties["gain"] = [self.cap.get(cv.CAP_PROP_GAIN), cv.CAP_PROP_GAIN]
            self.properties["exposure"] = [self.cap.get(cv.CAP_PROP_EXPOSURE), cv.CAP_PROP_EXPOSURE]

    # 设置参数
    def set(self, feature, *args):
        with self._lock:
            if not self.cap:
                return
            if self.properties[feature] is not None:
                if self.properties[feature][0] is not None:
                    self.cap.set(self.properties[feature][1], *args)
                    self.properties[feature][0] = self.cap.get(self.properties[feature][1])

    # 读取参数
    def get(self, feature):
        if not self.cap:
            return
        pro = self.properties.get(feature, None)
        if pro is not None:
            return pro[0]
        else:
            return None

    # 获取最新值
    def getLastImage(self):
        if not self.cap:
            return
        if (not self._readState) or (not isinstance(self._lastImg, np.ndarray)):
            return self.read()
        return self._lastImg

    # 判断相机是否正在读取
    def isReading(self):
        return self._readState

    # 读出数据
    def read(self, cache=True):
        with self._lock:
            self._readState = True
            if not self.cap:
                self._readState = None
                return
            for _ in range(int(not cache) + 1):
                begin = time.time()
                ret, image = self.cap.read()
                while not ret:
                    end = time.time() - begin
                    if end >= 2:
                        self._readState = None
                        raise ReadFailedError('Can"t read an image. Pass 2s')
                    ret, image = self.cap.read()
                time.sleep(0.05)
            self._lastImg = image
            self._readState = False
            return image

    # 释放相机
    def close(self):
        with self._lock:
            if not self.cap:
                return
            try:
                self.cap.release()
            except Exception as e:
                print(str(e))
            finally:
                self.cap = None

    # 移除
    def __del__(self):
        print('释放相机:{}'.format(self.name))
        self.close()


# 对图像进行处理，输入图像为灰度图
def imageProcess(img):
    """
    对图像进行处理，可以用同名函数覆盖
    :param img: 输入的图像
    :return: 调整后的图像
    """
    # 中值滤波消除椒盐噪声
    img = cv.medianBlur(img, 5)
    # 自适应设置阈值
    # img = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_MEAN_C,
    #                          cv.THRESH_BINARY, 7, 0)
    _, img = cv.threshold(img, 60, 255, cv.THRESH_BINARY)
    # detected_edges = cv.Canny(img, 0, 0, 5)
    # mask = detected_edges != 0
    # img = img * (mask[:, :].astype(img.dtype))
    return img


# 图像预处理
class Pretreatment(object):
    """
    创建预处理对象，专门用于保存真实图像及相关尺寸。

    proprety:
        size-代表选择图像ROI的尺寸
        _pretimgs-初始图像的预处理结果

    method:
        __init__-初始化，并获得图像的尺寸，标准图像等
        selectROI-以UI的方式选择图像
        getROI-获得ROI图像
        imageProcess-图像处理
        process-获得所有相机拍摄的ROI图像
    """

    # 获得标准图像
    def getStandardImages(self):
        return self._pretimgs

    # size表示我们预先知道了ROI的尺寸
    def __init__(self, timgs, size=None):
        if not size:
            # 感兴趣区域的尺寸，在实例中size对应于多个摄像机拍摄图像的感兴趣区域的尺寸。
            self.size = self.selectROI(timgs)
        else:
            self.size = size
        self._timgs = timgs

    def preProcess(self):
        self._pretimgs = self.process(self._timgs)

    # 选择合适的区域
    def selectROI(self, imgs):
        size = []
        for img in imgs:
            times = 0
            while True:
                r = cv.selectROI(img)
                times += 1
                if all(r):
                    break
                if times > 10:
                    print('未能正确获取大小')
                    r = [1, 1, 1, 1]
                    break
            cv.destroyAllWindows()  # 这条语句防止有多余的窗口残留
            size.append(r)
        return tuple(size)

    def getROI(self, num, img):
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        size = self.size[num]
        temp = img[:, size[0]:(size[0] + size[2])]
        return temp[size[1]:(size[1] + size[3]), :]

    def imageProcess(self, img):
        return imageProcess(img)

    def process(self, imgs):
        preimgs = []
        for ind, img in enumerate(imgs):
            if np.any(img) is None:
                preimgs.append(None)
                continue
            else:
                img = self.getROI(ind, img)
                img = self.imageProcess(img)
                preimgs.append(img)
        return preimgs


class Evaluation(object):
    """
    构建适合的Evaluation，实现某种Train算法。

    proprety:
        _pretimgs-初始图像的预处理结果

    method:
        __init__-初始化
    """


    # 导入相应的标准图像
    def __init__(self, pretimgs):
        self._pretimgs = pretimgs
        self.middles = []
        self.init()

    def init(self):
        for img in self._pretimgs:
            arg = np.argwhere(img == 255)
            if len(arg) == 0:
                self.middles.append(np.array([0, 0]))
            else:
                self.middles.append(np.mean(arg, 0))

    def getInitMiddle(self):
        return self.middles

    # 计算整体偏移，使得整体偏移最小
    def compute(self, imgs):
        cdeviations = []
        for ind, img in enumerate(imgs):
            arg = np.where(img == 255)
            middle = np.array([np.mean(i, 0) for i in arg])
            cdeviations.append(middle - self.middles[ind])
        return cdeviations


def resize(*imgs, ratio=1):
    """
    调整多幅图像，使得所有图像的长宽一样。
    :param imgs: 包含多幅图像的列表
    :param ratio: 缩放因子
    :return: 调整后包含多幅图像的列表
    """
    height, width = np.min([img.shape for img in imgs], axis=0)
    height = int(height*ratio)
    width = int(width*ratio)
    postimgs = [cv.resize(img, (width, height), interpolation=cv.INTER_CUBIC) for img in imgs]
    return postimgs

def rotate_bound(image, angle):
    """
    将图像旋转特定角度
    :param image: 可以多维度的图像
    :param angle: 旋转角度
    :return: 旋转后的图像
    """
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
 
    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
 
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
 
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
 
    # perform the actual rotation and return the image
    return cv.warpAffine(image, M, (nW, nH))

def showMultiplyCameras(cms, rotate=0, ratio=1):
    """
    显示多个摄像机拍摄的图像，默认rotate=0不旋转
    :param cms: 包含Camera相机对象的序列
    :param rotate: 旋转尺度，可以为数值或者与cms相同长度的序列
    :param ratio: 图像等比例缩放因子
    :return:
    """
    if isinstance(rotate, (int, float)):
        rotates = [rotate]*len(cms)
    elif isinstance(rotate, (tuple, list)) and len(rotate) == len(cms):
        rotates = rotate
    else:
        print("Error: parameter 'rotate' must be a number or sequence of the same length as 'cms'")
        return
    # 创建窗口
    cv.namedWindow('frame', cv.WINDOW_AUTOSIZE)
    while cv.getWindowProperty('frame', cv.WINDOW_NORMAL) >= 0:
        # 采用轮询的方式遍历所有的camera
        # Capture frame-by-frame
        frames = readImages(cms)
        # Our operations on the frame come here
        imgs = [rotate_bound(cv.cvtColor(frame, cv.COLOR_BGR2GRAY), angle=rotates[ind]*90) for ind, frame in enumerate(frames)]
        # 对图像进行缩放
        postimgs = resize(*imgs, ratio=ratio)
        # 整合
        total = np.hstack(postimgs)
        # Display the resulting frame
        cv.imshow('frame', total)
        # wait 1ms
        if cv.waitKey(1) == ord('q') or cv.waitKey(1) & 0xff == ord('q'):
            break

    # When everything done, close window
    cv.destroyAllWindows()


def openCameras(cmsid, names=None):
    """
    打开多个相机，并赋予相机对象特定名称
    :param cmsid: 可以为包含相机的id号的序列，或者单个id值，用于连接相机
    :param names: 相机的唯一名称，可以为长度与cmsid相同的序列，或者为单个名称，默认为None
    :return: 返回包含相机对象的序列
    """
    cms = []
    if getattr(cmsid, '__len__', None):
        for ind, cid in enumerate(cmsid):
            print('尝试打开相机{}'.format(cid))
            if names is None:
                cm = Camera(str(cid))
                cm.connect(cid)
            else:
                cm = Camera(names[ind])
                cm.connect(cid)
            print('相机{}打开成功'.format(cid))
            print('相机{}的属性为:'.format(cid))
            print(cm.properties)
            cms.append(cm)
    else:
        print('尝试打开相机{}'.format(cmsid))
        if names is None:
            cm = Camera(str(cmsid))
            cm.connect(cmsid)
        else:
            cm = Camera(str(names))
            cm.connect(cmsid)
        print('相机{}打开成功'.format(cmsid))
        print('相机{}的属性为:'.format(cmsid))
        print(cm.properties)
        cms.append(cm)
    return tuple(cms)


def readImages(cms):
    """
    从多个相机对象中读取图片
    :param cms: 包含Camera对象的序列
    :return: 包含numpy数组的序列，实际为读取的图像
    """
    return tuple([cm.read() for cm in cms])


def saveImage(img, filename='default.jpg', dirRoot=''):
    """
    用于保存单张图像到指定名称中
    :param dirRoot: 保存图像的根目录
    :param filename: 图像的名称
    :param img: 图像数组
    """
    filename = os.path.join(dirRoot, filename)
    cv.imwrite(filename, img)


def saveImages(imgs, dirPath='', dirRoot='.'):
    """
    用于保存多张图像到同一目录
    :param dirRoot: 保存图像的根目录
    :param dirPath: 保存图像集合的目录
    :parma imgs: 图像数组的序列或集合
    """
    path = os.path.join(dirRoot, dirPath)
    if not os.path.exists(path):
        os.mkdir(path)
    for ind, img in enumerate(imgs):
        ind = str(ind) + '.jpg'
        filename = os.path.join(path, ind)
        cv.imwrite(filename, img)
