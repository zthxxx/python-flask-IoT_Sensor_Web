# -*- coding: utf-8 -*-
import pymongo
import time
from pymongo import MongoClient
from DataBaseOperation.MongoDBOperation import MongoDBOperation

class SensorMongoORM(object):
    def __init__(self,host="localhost",port=27017,database_name="", collection_name="",user=None,passwd=None):
        self.collection_name = collection_name
        self.__mongo = MongoDBOperation(host=host,port=port,user=user,passwd=passwd,)
        self.__mongo.switchDBCollect(database_name,collection_name)

    def insert_with_time(self,json_obj):
        if('Owner' in json_obj):
            json_obj["current_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            return self.__mongo.insert(json_obj,collection=[self.collection_name,json_obj['Owner']])

    def find_latest_one(self,username):
        aggregate_command = [{'$sort':{'current_time':pymongo.DESCENDING}},{'$limit':1}]
        result = list(self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username]))
        if(len(result) > 0):
            last_order = result[0]
            if(('_id') in last_order):
                del last_order['_id']
            return last_order
        else:
            return None

    def find_user_password(self,username):
        password = None
        if(isinstance(username,str) is True):
            password_obj = self.__mongo.find_one({'UserName':username},{'Password':1,'_id':0},collection=[self.collection_name,"UserInfo"])
            if(password_obj is not None):
                password = password_obj.get('Password',None)
        return password

    def remove_all(self):
        return self.__mongo.remove({},collection=None)

    def find_one(self):
        return self.__mongo.find_one(collection=None)

    def aggregate_field_area_list(self,username,field_name,limit_length=None):
        aggregate_command = [{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1}}]
        if(limit_length is not None):
            aggregate_command[0] = {'$sort':{'current_time':pymongo.DESCENDING}}
            aggregate_command.insert(1,{'$limit':limit_length})
            aggregate_command.insert(2,{'$sort':{'current_time':pymongo.ASCENDING}})
        result = self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username])
        return [account.get(field_name) for account in result]

    def aggregate_field_list(self,username,field_name):
        return self.aggregate_field_area_list(username,field_name,None)

    def aggregate_field_Recent_order_list(self,username,field_name,limit_time):
        aggregate_command = [{'$match':{'current_time':{'$gt':limit_time}}},{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1}}]
        result = self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username])
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


    print(dict(mongo_conn.find_latest_one()))
    # print(mongo_conn.findOne().get('currentime'))
    print(mongo_conn.aggregate_field_list('test_count'))










