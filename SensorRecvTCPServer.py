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
import threading
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

"""
#StreamRequestHandler，并重写handle方法
#（StreamRequestHandler继承自BaseRequestHandler）
"""
class SensorRecvTCPServerHandler(StreamRequestHandler):
    mongo_write_conn = None
    sensor_data_packet_count = 0
    callback_list = set()
    def __init__(self,*args,**kwargs):
        if(isinstance(SensorRecvTCPServerHandler.mongo_write_conn, SensorMongoORM) is not True):
            initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
            databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
            databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
            SensorRecvTCPServerHandler.mongo_write_conn = SensorMongoORM(**databaseConnectConfig)
            print(SensorRecvTCPServerHandler.mongo_write_conn)
        StreamRequestHandler.__init__(self,*args,**kwargs)

    @classmethod
    def add_callback(cls,fun):
        SensorRecvTCPServerHandler.callback_list.add(fun)

    @classmethod
    def del_callback(cls,fun):
        SensorRecvTCPServerHandler.callback_list.discard(fun)

    def handle(self):
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' TCP client from ' + str(self.client_address) + ' linked in.')
        protocol_analyzer = CommunicationProtocolPacketAnalysis()
        while True:
            try:
                data = self.rfile.read(1)
                if data:
                    protocol_analyzer.put_FIFO_byte_data(data)
                    for json_data in protocol_analyzer.load_JSON_data_from_queue():
                        if(json_data is None):  continue
                        SensorRecvTCPServerHandler.sensor_data_packet_count += 1
                        print(time.ctime(), SensorRecvTCPServerHandler.sensor_data_packet_count)
                        if(isinstance(SensorRecvTCPServerHandler.mongo_write_conn, SensorMongoORM)):
                            SensorRecvTCPServerHandler.mongo_write_conn.insertWithTime(json_data)
                            if( '_id' in json_data):
                                del json_data['_id']
                        for callback_fun in SensorRecvTCPServerHandler.callback_list:
                            if(isinstance(json_data,dict)):
                                callback_fun(json_data)
                            # try:
                            #     callback_fun(json_data)
                            # except:
                            #     print('SensorRecvTCPServer callback function get a error.')
                                # SensorRecvTCPServerHandler.del_callback(callback_fun)
                else:
                    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' TCP client from ' + str(self.client_address) + ' closed.')
                    break
            except:
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' TCP client from ' + str(self.client_address) + ' error.')
                traceback.print_exc()
                break

def sensor_recv_TCPserver_run():
    initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
    TcpListingConfig = initializationConfigParser.GetAllNodeItems("TcpServerListeningSocket")
    TcpListingConfig["listening_port"] = int(TcpListingConfig.get("listening_port"))
    TcpAddress = (TcpListingConfig.get("tcpserver_host"), TcpListingConfig.get("listening_port"))
    print(TcpAddress)
    server = ThreadingTCPServer(TcpAddress, SensorRecvTCPServerHandler)
    print('request_tcpserver_thread start')
    serve_forever_thread = threading.Thread(target=server.serve_forever)
    serve_forever_thread.start()
    print('request_tcpserver_thread running')

if __name__ == "__main__":
    def show_data(data):
        print(data)
    SensorRecvTCPServerHandler.add_callback(show_data)
    sensor_recv_TCPserver_run()
