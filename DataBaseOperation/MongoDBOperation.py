# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient

class MongoDBOperation(object):
    def __init__(self,host="localhost",port=27017,user=None,passwd=None):
        self.__mongo_client = MongoClient(host, int(port))
        self.database = None
        self.collection = None
        if user is not None:
            self.__mongo_client.admin.authenticate(user, passwd)

    def __del__(self):
        self.CloseConnect()
        print('MongoDB client closed')

    def CloseConnect(self):
        if isinstance(self.__mongo_client, MongoClient):
            self.__mongo_client.close()

    def IsRaiseError(methodName):
        def TryUseMethod(*args, **kw):
            try:
                if callable(methodName):
                    return methodName(*args, **kw)
            except Exception as errorInfor:
                print(methodName,errorInfor)
                return None
        return TryUseMethod

    def get_dict_deep_layer(self,dict_base,layer_list):
        value = dict_base
        if isinstance(layer_list,list) is True:
            for layer in layer_list:
                value = value[layer]
        return value

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

    def collection_method(self,fun,*args,collection=None):
        if (collection is not None) and (isinstance(collection,list) is True):
            return getattr(self.get_dict_deep_layer(self.database,collection),fun)(*args)
        return getattr(self.collection,fun)(*args)

    def find(self,*args,collection=None):
        return self.collection_method('find',*args,collection=collection)

    def find_one(self,*args,collection=None):
        return self.collection_method('find_one',*args,collection=collection)

    def insert(self,*args,collection=None):
        return self.collection_method('insert',*args,collection=collection)

    def update(self,*args,collection=None):
        return self.collection_method('update',*args,collection=collection)

    def remove(self,*args,collection=None):
        return self.collection_method('remove',*args,collection=collection)

    def aggregate(self,*args,collection=None):
        return self.collection_method('aggregate',*args,collection=collection)


if __name__ == '__main__':
    parameter = {'host':"localhost",'port':27017,'user':'root','passwd':''}
    mongo_write_conn = MongoDBOperation(**parameter)
    mongo_write_conn.switchDBCollect('IoTSensor', 'SmartHomeData')
    mongo_write_conn.insert({"neme": "test", 'type': 'Test'})
    print(mongo_write_conn.find(None).count())
    print(mongo_write_conn.find_one(None))
    mongo_write_conn.remove({"neme": "test"})
    print(mongo_write_conn.find(None).count())













