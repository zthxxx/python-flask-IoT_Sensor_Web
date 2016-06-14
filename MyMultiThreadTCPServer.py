# encoding: utf-8
#python2.7下有中文的地方要加u""
from multiprocessing import freeze_support
freeze_support()
try:
    import queue as Queue
except:
    import Queue
import sys
sys.setrecursionlimit(1000000)
import json

from  ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from  ServerClientSocket.ProcessingQueueManager import ProcessingQueueManager
try:
    from SocketServer import ThreadingTCPServer
    from SocketServer import StreamRequestHandler
except:
    import operator
    from socketserver import ThreadingTCPServer
    from socketserver import StreamRequestHandler
import traceback
from TianMaoProtocol.TianMaoProtocol import CommunicationProtocolPacketAnalysis

"""
#StreamRequestHandler，并重写handle方法
#（StreamRequestHandler继承自BaseRequestHandler）
"""
class MyStreamRequestHandlerr(StreamRequestHandler):
    # def __init__(self,*args,**kwargs):
    #     super(StreamRequestHandler,self).__init__(*args,**kwargs)
    #     self.queueManager = kwargs.get("manager",None)

    def handle(self):
        protocol_analyzer = CommunicationProtocolPacketAnalysis()
        while True:
            try:
                data = self.rfile.read(1)
                if data:
                    protocol_analyzer.put_FIFO_byte_data(data)
                    for json_data in protocol_analyzer.load_JSON_data_from_queue():
                        if(json_data is None):  break
                        if(isinstance(queueManager,ProcessingQueueManager)):
                            pass
                            queueManager.PutTaskQueueOnlyObj(json_data)
                        # print(u"设备名: %s" % json_data.pop("Device"))
                        # print(u"设备地址: %s" % json_data.pop("Address"))
                        # print(u"消息类型: %s" % json_data.pop("InfoType"))
                        for eachKey in json_data:
                            print("%s: %s" % (eachKey,json_data[eachKey]))

                else:
                    break
            except:
                traceback.print_exc()
                break


if __name__ == "__main__":

    host = ""       #主机名，可以是ip,像localhost的主机名,或""
    port = 31511
    addr = (host, port)
    initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
    serverConnectConfig = initializationConfigParser.GetAllNodeItems("ServerSocket")
    serverConnectConfig["port"] = int(serverConnectConfig.get("port"))
    queueManager = ProcessingQueueManager()
    queueManager.StartManager(**serverConnectConfig)
    print('start')
    #ThreadingTCPServer从ThreadingMixIn和TCPServer继承
    #class ThreadingTCPServer(ThreadingMixIn, TCPServer): pass
    server = ThreadingTCPServer(addr, MyStreamRequestHandlerr)
    #启动服务监听
    server.serve_forever()
