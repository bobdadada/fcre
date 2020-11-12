# -*- coding: utf-8 -*-

__all__ = ['Experiment', 'Train']

import threading

class Experiment(threading.Thread):
    """
    实验类，以子线程的方式运行对应的函数。

    proprety:
        _stopped-线程停止标志
        _running-线程正在运行标志
        _target_fun-实验的主函数
    method:
        __init__-初始化，输入实验运行的主函数
        start-线程开始函数
        run-线程运行函数
        stop-线程停止函数
        isStopped-判断线程是否停止
        isRunning-判断线程是否正在运行
    """
    def __init__(self, target_func):
        super(Experiment, self).__init__()
        self._stopped = False
        self._running = False
        self._target_func = target_func

    def start(self):
        self._running = True
        super(Experiment, self).start()

    def run(self):
        while not self._stopped:
            self._target_func()
        print('实验结束，请检查仪器是否运行正常，欢迎下次使用')

    def stop(self):
        self._stopped = True
        self._running = False

    def isStopped(self):
        return self._stopped

    def isRunning(self):
        return self._running

try:
    import keras
    import numpy as np
    from keras.models import Sequential
    from keras.layers import Dense, Activation
    class Train(object):
        """
        运用机器学习的方式获得图像偏移与平台偏移之间的关系。

        proprety:
            _dataset_train-bool值，判断是否存在训练集合
            _dataset_test-bool值，判断是否存在测试集合
            p-训练数据和测试数据之间的比例
            model-训练模型
        method:
            __init__-初始化
            setModel-导入预先编译好的模型，参考keras model
            setupModel-建立默认的模型，这个可以在子类中覆盖掉
            train-训练模型
            save-保存模型到目标位置
            put-以元素的方式导入dataset，用于训练
            compute-预测结果
        """

        def __init__(self, model=None):
            self._dateset_train = False
            self._dateset_test = False
            self.p = 0.8  # 训练数据和测试数据之间的比例
            if not model:
                self.model = self.setupModel()
            else:
                self.model = model

        def setModel(self, model):
            self.model = model

        def setupModel(self):
            model = Sequential()
            model.add(Dense(12, input_dim=4, kernel_initializer='uniform', activation='relu'))
            model.add(Dense(8, kernel_initializer='uniform', activation='relu'))
            model.add(Dense(3, kernel_initializer='uniform', activation='sigmoid'))
            # compile 编译
            model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
            return model

        def train(self):
            self.model.fit(self.x_train, self.y_train, batch_size=72, epochs=10)
            # 评估模型
            loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
            print('\ntest loss:', loss)
            print('accuracy:', accuracy)

        def save(self, path):
            print('save model in {}'.format(path))
            self.model.save(path)

        def put(self, x, y):
            x = np.array(x).reshape(-1)
            y = np.array(y).reshape(-1)
            if (not x.any()) and (not y.any()):
                return
            if np.random.rand() < self.p:
                if not self._dateset_train:
                    self.x_train = x
                    self.y_train = y
                    self._dateset_train = True
                else:
                    self.x_train = np.vstack((self.x_train, x))
                    self.y_train = np.vstack((self.y_train, y))
            else:
                if not self._dateset_test:
                    self.x_test = x
                    self.y_test = y
                    self._dateset_test = True
                else:
                    self.x_test = np.vstack((self.x_test, x))
                    self.y_test = np.vstack((self.y_test, y))

        def compute(self, cdeviations):
            x = np.array(cdeviations).reshape(1,-1)
            y = self.model.predict(x)
            return y[0].tolist()
except ImportError as e:
    print(e)
    Train = None
    

if __name__ == '__main__':
    t = Train()
    for i in range(200):
        t.put([[1, 3], [2, 4]], [1, 3, 2])
    t.train()
