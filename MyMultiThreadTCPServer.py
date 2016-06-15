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
import time

from  ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
# from  ServerClientSocket.ProcessingQueueManager import ProcessingQueueManager
try:
    from SocketServer import ThreadingTCPServer
    from SocketServer import StreamRequestHandler
except:
    import operator
    from socketserver import ThreadingTCPServer
    from socketserver import StreamRequestHandler
import traceback
from TianMaoProtocol.TianMaoProtocol import CommunicationProtocolPacketAnalysis
from DataBaseOperation.SensorMongoORM import SensorMongoORM

mongo_write_conn = None
sensor_data_packet_count = 0

"""
#StreamRequestHandler，并重写handle方法
#（StreamRequestHandler继承自BaseRequestHandler）
"""
class MyStreamRequestHandler(StreamRequestHandler):
    # def __init__(self,*args,**kwargs):
    #     super(StreamRequestHandler,self).__init__(*args,**kwargs)
    #     self.queueManager = kwargs.get("manager",None)

    def handle(self):
        global mongo_write_conn
        global sensor_data_packet_count
        protocol_analyzer = CommunicationProtocolPacketAnalysis()
        while True:
            try:
                data = self.rfile.read(1)
                if data:
                    protocol_analyzer.put_FIFO_byte_data(data)
                    for json_data in protocol_analyzer.load_JSON_data_from_queue():
                        if(json_data is None):  break
                        if(isinstance(mongo_write_conn, SensorMongoORM)):
                            pass
                            mongo_write_conn.insertWithTime(json_data)
                        sensor_data_packet_count += 1
                        print(time.ctime(),sensor_data_packet_count)
                        # for eachKey in json_data:
                        #     print("%s: %s" % (eachKey,json_data[eachKey]))
                else:
                    break
            except:
                traceback.print_exc()
                break

def request_tcpserver_run():
    global mongo_write_conn
    initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
    databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
    databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
    mongo_write_conn = SensorMongoORM(**databaseConnectConfig)

    TcpListingConfig = initializationConfigParser.GetAllNodeItems("TcpServerListeningSocket")
    TcpListingConfig["listening_port"] = int(TcpListingConfig.get("listening_port"))
    TcpAddress = (TcpListingConfig.get("tcpserver_host"), TcpListingConfig.get("listening_port"))
    server = ThreadingTCPServer(TcpAddress, MyStreamRequestHandler)

    # print(mongo_write_conn.aggregateFieldToList('test_count'))
    print('request_tcpserver_run start')
    server.serve_forever() #启动服务监听


if __name__ == "__main__":
    request_tcpserver_run()
