# encoding: utf-8
try:
    import queue as Queue
except:
    import Queue
import sys
sys.setrecursionlimit(1000000)
import json

class PacketBlock(object):
    PROTOCOL_PACKET_HEAD_LENGTH = 4
    PROTOCOL_PACKET_CONSISTENT_LENGTH = 11 + PROTOCOL_PACKET_HEAD_LENGTH
    def __init__(self):
        self.head = [0] * self.PROTOCOL_PACKET_HEAD_LENGTH
        self.targetAddress = 0
        self.sourceAddress = 0
        self.targetAddressBytes = [0] * 2
        self.sourceAddressBytes = [0] * 2
        self.index = 0
        self.indexBytes = [0] * 2
        self.functionWord = 0
        self.headCheckSum = 0
        self.messageDataLength = 0
        self.messageDataLengthBytes = [0] * 2
        self.messageData = []
        self.messageDataCheckSum = 0

    def CalculatePacketBlockHeadCheckSum(self):
        headCheckSum = sum(self.head)
        headCheckSum += sum(self.targetAddressBytes)
        headCheckSum += sum(self.sourceAddressBytes)
        headCheckSum += sum(self.indexBytes)
        headCheckSum += self.functionWord
        headCheckSum += sum(self.messageDataLengthBytes)
        return headCheckSum % (0x100)       #相当于只取最低位

    def CalculatePacketBlockMessageDataCheckSum(self):
        messageDataCheckSum = sum(self.messageData)
        return messageDataCheckSum % (0x100)#相当于只取最低位

"""
#先put进FIFO，再检查是否收包完整。
protocol_analyzer.put_FIFO_byte_data(data)
while(True):
    json_data = protocol_analyzer.load_JSON_data_from_queue()
    if(json_data is None):  break
    #至此json_data为json对象字典格式，直接使用
"""
class CommunicationProtocolPacketAnalysis(object):

    Protocol_HeadData = [0xEF,0x02,0xAA,0xAA]

    def __init__(self):
        self.packetBlock = PacketBlock()
        self.receiveBytesDataFIFO = Queue.Queue()
        self.packetBlockQueue = Queue.Queue()
        self.isCommunicationPacketReceiveEnd = True

    def list_to_int(self,bytesList):
        intValue = 0
        if(isinstance(bytesList, list)):
            length = len(bytesList)
            for count in range(0,length):
                intValue += bytesList[count] << (8*count)
            return intValue
        else:
            return None

    def queue_data_pop(self, stream, outCount):
        if(self.receiveBytesDataFIFO.qsize() < outCount):
            return None
        if(outCount == 1 and stream is None):
            return self.receiveBytesDataFIFO.get()
        if(stream is None or len(stream) < outCount):
            return None
        for count in range(0,outCount):
            stream[count] = self.receiveBytesDataFIFO.get()

    def load_data_from_queue(self):#将数据流解包在类中，并存入Queue中
        isHeadAllEqual = False
        while(True):
            if(self.isCommunicationPacketReceiveEnd is True):
                if(isHeadAllEqual is not True):
                    if(self.receiveBytesDataFIFO.qsize() < self.packetBlock.PROTOCOL_PACKET_CONSISTENT_LENGTH):
                        return None
                    while True:     #此处为接收帧头
                        if (self.receiveBytesDataFIFO.qsize() <= 0):
                            return None
                        for count in range(0,len(self.packetBlock.head)-1):
                            self.packetBlock.head[count] = self.packetBlock.head[count+1]
                        self.packetBlock.head[-1] = self.receiveBytesDataFIFO.get()
                        if(self.packetBlock.head == self.Protocol_HeadData):#等于0表示相同
                            isHeadAllEqual = True
                            break
                if(self.receiveBytesDataFIFO.qsize() < self.packetBlock.PROTOCOL_PACKET_CONSISTENT_LENGTH - len(self.packetBlock.head)):
                    return None
                self.queue_data_pop(self.packetBlock.targetAddressBytes, 2)
                self.queue_data_pop(self.packetBlock.sourceAddressBytes, 2)
                self.queue_data_pop(self.packetBlock.indexBytes, 2)
                self.packetBlock.functionWord = self.queue_data_pop(None, 1)
                self.queue_data_pop(self.packetBlock.messageDataLengthBytes, 2)
                self.packetBlock.messageDataCheckSum = self.queue_data_pop(None, 1)
                if(self.packetBlock.messageDataCheckSum != self.packetBlock.CalculatePacketBlockHeadCheckSum()):
                    isHeadAllEqual = False
                    self.packetBlock.head = [0] * self.packetBlock.PROTOCOL_PACKET_HEAD_LENGTH
                    continue
                self.packetBlock.targetAddress = self.list_to_int(self.packetBlock.targetAddressBytes)
                self.packetBlock.sourceAddress = self.list_to_int(self.packetBlock.sourceAddressBytes)
                self.packetBlock.index = self.list_to_int(self.packetBlock.indexBytes)
                self.packetBlock.messageDataLength = self.list_to_int(self.packetBlock.messageDataLengthBytes)
            self.isCommunicationPacketReceiveEnd = False
            if(self.receiveBytesDataFIFO.qsize() < self.packetBlock.messageDataLength + 1):
                return None
            self.packetBlock.messageData = [0] * self.packetBlock.messageDataLength
            self.queue_data_pop(self.packetBlock.messageData, self.packetBlock.messageDataLength)
            self.packetBlock.messageDataCheckSum = self.queue_data_pop(None, 1)
            self.isCommunicationPacketReceiveEnd = True
            isHeadAllEqual = False
            if(self.packetBlock.messageDataCheckSum == self.packetBlock.CalculatePacketBlockMessageDataCheckSum()):
                self.packetBlockQueue.put(self.packetBlock)
            self.packetBlock = PacketBlock()

    def put_FIFO_byte(self,byte):
        self.receiveBytesDataFIFO.put(byte)

    def put_FIFO_bytes_list(self, bytesList):
        for oneByte in bytesList:
            self.put_FIFO_byte(oneByte)

    def put_FIFO_byte_data(self,data):
        if(isinstance(data,list) or isinstance(data,str) or isinstance(data,bytes)):
            try:
                bytesList= bytearray(data)
                self.put_FIFO_bytes_list(bytesList)
            except:
                pass

    def load_JSON_data_from_queue(self):
        self.load_data_from_queue()
        while(self.packetBlockQueue.qsize() > 0):
            packet_block = self.packetBlockQueue.get()
            packet_JSON_data_string = "".join(map(chr,packet_block.messageData))
            try:
                json_data = json.loads(packet_JSON_data_string) #至此数据转为json字典对象
                yield json_data
            except:
                continue











