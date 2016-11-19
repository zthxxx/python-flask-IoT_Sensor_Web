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
    PROTOCOL_STANDARD_HEAD_DATA = [0xEF,0x02,0xAA,0xAA]

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
    if json_data is None):  break
    #至此json_data为json对象字典格式，直接使用
"""
class CommunicationProtocolPacketAnalysis(object):

    Protocol_HeadData = PacketBlock.PROTOCOL_STANDARD_HEAD_DATA[:]
    FunctionWord_TypeDef = {
        'FunctionWord_Null': 0,
        'FunctionWord_Handshake': 0xF0,
        'FunctionWord_Acknowledgement': 0xF1,
        'FunctionWord_RegisterDevice': 0xF2,
        'FunctionWord_Dormant': 0xF3,
        'FunctionWord_StartUP': 0xF4,
        'FunctionWord_Data': 0xF5,
        'FunctionWord_Logout': 0xF6,
        'FunctionWord_Reboot': 0xF7,
        'FunctionWord_Shutdown': 0xF8
    }
    def __init__(self):
        self.packetBlock = PacketBlock()
        self.receiveBytesDataFIFO = Queue.Queue()
        self.packetBlockQueue = Queue.Queue()
        self.isCommunicationPacketReceiveEnd = True

    def list_to_int(self,bytesList):
        intValue = 0
        if isinstance(bytesList, list):
            length = len(bytesList)
            for count in range(0,length):
                intValue += bytesList[count] << (8*count)
            return intValue
        else:
            return None

    def queue_data_pop(self, stream, outCount):
        if self.receiveBytesDataFIFO.qsize() < outCount:
            return None
        if outCount == 1 and stream is None:
            return self.receiveBytesDataFIFO.get()
        if stream is None or len(stream) < outCount:
            return None
        for count in range(0,outCount):
            stream[count] = self.receiveBytesDataFIFO.get()

    def load_data_from_queue(self):#将数据流解包在类中，并存入Queue中
        isHeadAllEqual = False
        while(True):
            if self.isCommunicationPacketReceiveEnd is True:
                if isHeadAllEqual is not True:
                    if self.receiveBytesDataFIFO.qsize() < self.packetBlock.PROTOCOL_PACKET_CONSISTENT_LENGTH:
                        return None
                    while True:     #此处为接收帧头
                        if self.receiveBytesDataFIFO.qsize() <= 0:
                            return None
                        for count in range(0,len(self.packetBlock.head)-1):
                            self.packetBlock.head[count] = self.packetBlock.head[count+1]
                        self.packetBlock.head[-1] = self.receiveBytesDataFIFO.get()
                        if self.packetBlock.head == self.Protocol_HeadData:#等于0表示相同
                            isHeadAllEqual = True
                            break
                if self.receiveBytesDataFIFO.qsize() < self.packetBlock.PROTOCOL_PACKET_CONSISTENT_LENGTH - len(self.packetBlock.head):
                    return None
                self.queue_data_pop(self.packetBlock.targetAddressBytes, 2)
                self.queue_data_pop(self.packetBlock.sourceAddressBytes, 2)
                self.queue_data_pop(self.packetBlock.indexBytes, 2)
                self.packetBlock.functionWord = self.queue_data_pop(None, 1)
                self.queue_data_pop(self.packetBlock.messageDataLengthBytes, 2)
                self.packetBlock.headCheckSum = self.queue_data_pop(None, 1)
                if self.packetBlock.headCheckSum != self.packetBlock.CalculatePacketBlockHeadCheckSum():
                    isHeadAllEqual = False
                    self.packetBlock.head = [0] * self.packetBlock.PROTOCOL_PACKET_HEAD_LENGTH
                    continue
                self.packetBlock.targetAddress = self.list_to_int(self.packetBlock.targetAddressBytes)
                self.packetBlock.sourceAddress = self.list_to_int(self.packetBlock.sourceAddressBytes)
                self.packetBlock.index = self.list_to_int(self.packetBlock.indexBytes)
                self.packetBlock.messageDataLength = self.list_to_int(self.packetBlock.messageDataLengthBytes)
            self.isCommunicationPacketReceiveEnd = False
            if self.receiveBytesDataFIFO.qsize() < self.packetBlock.messageDataLength + 1:
                return None
            self.packetBlock.messageData = [0] * self.packetBlock.messageDataLength
            self.queue_data_pop(self.packetBlock.messageData, self.packetBlock.messageDataLength)
            self.packetBlock.messageDataCheckSum = self.queue_data_pop(None, 1)
            self.isCommunicationPacketReceiveEnd = True
            isHeadAllEqual = False
            if self.packetBlock.messageDataCheckSum == self.packetBlock.CalculatePacketBlockMessageDataCheckSum():
                self.packetBlockQueue.put(self.packetBlock)
            self.packetBlock = PacketBlock()

    def put_FIFO_byte(self,byte):
        self.receiveBytesDataFIFO.put(byte)

    def put_FIFO_bytes_list(self, bytesList):
        for oneByte in bytesList:
            self.put_FIFO_byte(oneByte)

    def put_FIFO_byte_data(self,data):
        if isinstance(data,list) or isinstance(data,str) or isinstance(data,bytes):
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


class AssembleCommunicationProtocolPacket(object):
    Protocol_HeadData = PacketBlock.PROTOCOL_STANDARD_HEAD_DATA[:]
    Protocol_PacketSendIndex = 0
    Protocol_LocalhostAddress = 0x0001
    FunctionWord_TypeDef = {
        'FunctionWord_Null': 0,
        'FunctionWord_Handshake': 0xF0,
        'FunctionWord_Acknowledgement': 0xF1,
        'FunctionWord_RegisterDevice': 0xF2,
        'FunctionWord_Dormant': 0xF3,
        'FunctionWord_StartUP': 0xF4,
        'FunctionWord_Data': 0xF5,
        'FunctionWord_SetProperty': 0xF6,
        'FunctionWord_Logout': 0xF7,
        'FunctionWord_Reboot': 0xF8,
        'FunctionWord_Shutdown': 0xF9
    }
    def __init__(self):
        pass

    def int_to_list(self, int_data, bytes_length):
        bytes_list = bytearray(int_data.to_bytes(bytes_length, byteorder='little'))
        return bytes_list

    def assemble_protocol_packet_block(self,target_address, source_address, function_word, message_data):
        packet_block = PacketBlock()
        message_data_length = len(message_data)
        packet_block.head = AssembleCommunicationProtocolPacket.Protocol_HeadData[:]
        packet_block.targetAddress = target_address
        packet_block.targetAddressBytes = self.int_to_list(target_address, len(packet_block.targetAddressBytes))
        packet_block.sourceAddress = source_address
        packet_block.sourceAddressBytes = self.int_to_list(source_address, len(packet_block.sourceAddressBytes))
        packet_block.index = AssembleCommunicationProtocolPacket.Protocol_PacketSendIndex
        packet_block.indexBytes = self.int_to_list(packet_block.index, len(packet_block.indexBytes))
        packet_block.functionWord = function_word
        packet_block.messageDataLength = message_data_length
        packet_block.messageDataLengthBytes = self.int_to_list(message_data_length, len(packet_block.messageDataLengthBytes))
        packet_block.headCheckSum = packet_block.CalculatePacketBlockHeadCheckSum()
        packet_block.messageData = bytearray(message_data)
        packet_block.messageDataCheckSum = packet_block.CalculatePacketBlockMessageDataCheckSum()
        AssembleCommunicationProtocolPacket.Protocol_PacketSendIndex += 1
        return packet_block

    def resolve_packet_struct_into_bytes(self, packet_block):
        bytes_offset = 0
        protocol_packet_length = packet_block.messageDataLength + packet_block.PROTOCOL_PACKET_CONSISTENT_LENGTH
        assembled_packet_bytes = bytearray(protocol_packet_length)
        subject = [
            packet_block.head,
            packet_block.targetAddressBytes,
            packet_block.sourceAddressBytes,
            packet_block.indexBytes,
            [packet_block.functionWord],
            packet_block.messageDataLengthBytes,
            [packet_block.headCheckSum],
            packet_block.messageData,
            [packet_block.messageDataCheckSum],
        ]

        for item in subject:
            bytes_length = len(item)
            assembled_packet_bytes[bytes_offset:bytes_offset + bytes_length] = bytearray(item)
            bytes_offset += bytes_length

        return assembled_packet_bytes


if __name__ == '__main__':
    packet_assemble = AssembleCommunicationProtocolPacket()
    message = {
        "InfoType": "Setting",
        "Owner":"admin",
        "Address":2,
        "SwitchSet":{
            "SwitchIndex":1,
            "StatusSet":True
        }
    }
    print(message)
    message_data = json.dumps(message).encode()
    packet_block = packet_assemble.assemble_protocol_packet_block(
        0x002,
        0x001,
        packet_assemble.FunctionWord_TypeDef["FunctionWord_SetProperty"],
        message_data
    )
    print(packet_block)
    assembled_packet_bytes = packet_assemble.resolve_packet_struct_into_bytes(packet_block)
    print(assembled_packet_bytes)





