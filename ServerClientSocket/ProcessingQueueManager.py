# -*- coding: utf-8 -*-
import dill
dill.detect.trace(True)
from multiprocessing.managers import BaseManager
from multiprocessing import freeze_support
freeze_support()
try:
    import queue as Queue
except:
    import Queue

class ProcessingQueueManager():

    taskQueue = Queue.Queue()
    resultQueue = Queue.Queue()

    def __init__(self):
        self.queueManager = None

    def __del__(self):
        if(self.queueManager != None):
            self.CloseManager()

    @classmethod
    def ReturnTaskQueue(cls):
        return cls.taskQueue

    @classmethod
    def ReturnResultQueue(cls):
        return cls.resultQueue

    def StartManager(self, serveraddress="Localhost", port=80, key=None):
        if(self.queueManager == None):
            try:
                key = key.encode("utf-8")
            except:
                pass
            BaseManager.register('GetTaskQueue', callable=ProcessingQueueManager.ReturnTaskQueue)
            BaseManager.register('GetResultQueue', callable=ProcessingQueueManager.ReturnResultQueue)
            queueManager = BaseManager(address=(serveraddress, port), authkey=key)
            queueManager.start()
            self.queueManager = queueManager

    def PutTaskQueue(self,object):
        taskqueue = self.queueManager.GetTaskQueue()
        taskqueue.put(object)

    def PutTaskQueueOnlyObj(self,object):
        taskqueue = self.queueManager.GetTaskQueue()
        print(taskqueue.qsize())
        while(taskqueue.empty() is False):
            try:
                taskqueue.get_nowait()
            except:
                pass
        taskqueue.put(object)

    def GetResultQueue(self):
        resultQueue = self.queueManager.GetResultQueue()
        return resultQueue

    def GetResultQueuePop(self):
        resultQueue = self.queueManager.GetResultQueue()
        if(resultQueue.qsize() > 0):
            return resultQueue.get()
        else:
            return None

    def GetResultQueuePopBlock(self, timeout=None):
        resultQueue = self.queueManager.GetResultQueue()
        return resultQueue.get(timeout=timeout)

    def GetTaskQueuePop(self):
        taskQueue = self.queueManager.GetTaskQueue()
        if(taskQueue.qsize() > 0):
            return taskQueue.get()
        else:
            return None

    def GetTaskQueuePopBlock(self, timeout=None):
        taskQueue = self.queueManager.GetTaskQueue()
        return taskQueue.get(timeout=timeout)

    def CloseManager(self):
        try:
            self.queueManager.shutdown()
            print("ProcessingQueueManager exit")
        except:
            pass


if __name__ == '__main__':
    freeze_support()
    server = ProcessingQueueManager()
    server.StartManager('127.0.0.1',5000,b'abc')
    print("OK")
    for n in range(100,110):
        server.PutTaskQueue(n)
        print("put %d" % n)

    for i in range(10):
        print(server.GetResultQueuePopBlock())


