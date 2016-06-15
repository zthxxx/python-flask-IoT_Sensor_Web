# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient

class MongoDBOperation:
    def __init__(self,host="localhost",port=27017,user=None,passwd=None):
        self.__mongo_client = MongoClient(host, int(port))
        self.database = None
        self.collection = None
        if(user is not None):
            self.__mongo_client.admin.authenticate(user, passwd)

    def __del__(self):
        self.CloseConnect()
        print('MongoDB client closed')

    def CloseConnect(self):
        if(isinstance(self.__mongo_client, MongoClient)):
            self.__mongo_client.close()

    def IsRaiseError(methodName):
        def TryUseMethod(*args, **kw):
            try:
                if(callable(methodName)):
                    return methodName(*args, **kw)
            except Exception as errorInfor:
                print(methodName,errorInfor)
                return None
        return TryUseMethod

    def getDatabaseNames(self):
        return self.__mongo_client.database_names()

    def switchDatabase(self,database_name):
        self.database = self.__mongo_client[database_name]

    def switchCollection(self,collection_name):
        self.collection = self.database[collection_name]

    def switchDBCollect(self,database_name,collection_name):
        self.switchDatabase(database_name)
        self.switchCollection(collection_name)
        return self.collection

    def find(self,*args):
        return self.collection.find(*args)

    def find_one(self,*args):
        return self.collection.find_one(*args)

    def insert(self,json_obj):
        return self.collection.insert(json_obj)

    def remove(self,json_obj):
        return self.collection.remove(json_obj)

    def aggregate(self,*args):
        return self.collection.aggregate(*args)

if __name__ == '__main__':
    parameter = {'host':"localhost",'port':27017,'user':'root','passwd':''}
    mongo_write_conn = MongoDBOperation(**parameter)
    mongo_write_conn.switchDBCollect('IoTSensor', 'SmartHomeData')
    mongo_write_conn.insert({"neme": "test", 'type': 'Test'})
    print mongo_write_conn.find(None).count()
    print mongo_write_conn.find_one(None)
    mongo_write_conn.remove({"neme": "test"})
    print mongo_write_conn.find(None).count()













