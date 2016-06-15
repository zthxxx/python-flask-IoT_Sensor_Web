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
        result =  list(self.__mongo.find({},{'_id':0}).sort("current_time",pymongo.DESCENDING))
        if(len(result) > 0):
            return result[0]
        else:
            return None

    def removeAll(self):
        return self.__mongo.remove({})

    def findOne(self):
        return self.__mongo.find_one()

    def aggregateFieldToList(self,field_name):
        # result = self.__mongo.find().sort("current_time",pymongo.ASCENDING)
        aggregate_command = [{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1}}]
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










