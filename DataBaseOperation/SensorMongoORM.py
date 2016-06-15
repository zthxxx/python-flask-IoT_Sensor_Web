# -*- coding: utf-8 -*-
import pymongo
import time
from pymongo import MongoClient
from DataBaseOperation.MongoDBOperation import MongoDBOperation

class SensorMongoORM:
    def __init__(self,host="localhost",port=27017,database_name="", collection_name="",user=None,passwd=None):
        self.__mongo = MongoDBOperation(host=host,port=port,user=user,passwd=passwd,)
        self.__mongo.switchDBCollect(database_name,collection_name)

    def insertWithTime(self,json_obj):
        json_obj["current_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return self.__mongo.insert(json_obj)

    def findLatestOne(self):
        aggregate_command = [{'$sort':{'current_time':pymongo.DESCENDING}},{'$limit':1}]
        result = list(self.__mongo.aggregate(aggregate_command))
        if(len(result) > 0):
            last_order = result[0]
            if(last_order.has_key('_id')):
                del last_order['_id']
            return last_order
        else:
            return None

    def removeAll(self):
        return self.__mongo.remove({})

    def findOne(self):
        return self.__mongo.find_one()

    def aggregateFieldToAreaList(self,field_name,limit_length=None):
        aggregate_command = [{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1}}]
        if(limit_length is not None):
            aggregate_command.insert(1,{'$limit':limit_length})
        result = self.__mongo.aggregate(aggregate_command)
        return [account.get(field_name) for account in result]

    def aggregateFieldToList(self,field_name):
        return self.aggregateFieldToAreaList(field_name,None)

    def aggregateFieldRecentOrderList(self,field_name,limit_time):
        aggregate_command = [{'$match':{'current_time':{'$gt':limit_time}}},{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1}}]
        result = self.__mongo.aggregate(aggregate_command)
        return [account.get(field_name) for account in result]


if __name__ == '__main__':
    parameter = {'host':"localhost",'port':27017,'database_name':'IoTSensor','collection_name':'SmartHomeData','user':'root','passwd':'MongoRoot'}
    mongo_conn = SensorMongoORM(**parameter)
    # mongo_conn.removeAll()
    # mongo_conn.insertWithTime({"test_count":1,'name':'moerngo'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":"dd",'name':'mot4ngo'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":9,'name':'mong45o'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":2,'name':'m6ongo'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":"ac",'name':'mogo'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":7,'name':'mong45o'})
    # time.sleep(1)
    # mongo_conn.insertWithTime({"test_count":4,'name':'1ngo'})


    print(dict(mongo_conn.findLatestOne()))
    # print(mongo_conn.findOne().get('currentime'))
    print(mongo_conn.aggregateFieldToList('test_count'))










