# -*- coding: utf-8 -*-
import pymongo
import time
from pymongo import MongoClient
from DataBaseOperation.MongoDBOperation import MongoDBOperation
from HashTools.MD5Tools import MD5_hash_string

class SensorMongoORM(object):
    def __init__(self,host="localhost",port=27017,database_name="", collection_name="",user=None,passwd=None):
        self.collection_name = collection_name
        self.__mongo = MongoDBOperation(host=host,port=port,user=user,passwd=passwd,)
        self.__mongo.switchDBCollect(database_name,collection_name)

    def add_user_info(self,username,password,terminal_list=[]):
        Terminals = []
        for terminal in terminal_list:
            if (("Address" in terminal) and ("SensorList" in terminal)):
                SensorList = terminal["SensorList"]
                sensor_list = []
                for sensor in SensorList:
                    if (("SensorType" in sensor) and ("DisplayName" in sensor) and ("QuantityUnit" in sensor)):
                        sensor_list.append({
                            "SensorType" : sensor["SensorType"],
                            "DisplayName" : sensor["DisplayName"],
                            "QuantityUnit" : sensor["QuantityUnit"]
                        })
                Terminals.append({
                    "Address" : terminal["Address"],
                    "SensorList" : sensor_list
                })
        return self.__mongo.insert({
            'UserName':username,
            'Password':password,
            'Terminal':Terminals
        },collection=[self.collection_name,"UserInfo"])

    def find_user_password(self,username):
        password = None
        if(isinstance(username,str) is True):
            password_obj = self.__mongo.find_one({'UserName':username},{'Password':1,'_id':0},collection=[self.collection_name,"UserInfo"])
            if(password_obj is not None):
                password = password_obj.get('Password',None)
        return password

    def update_user_password(self,username,new_password):
        result = self.__mongo.update({'UserName':username},{"$set":{"Password":new_password}},collection=[self.collection_name,"UserInfo"])
        return result

    def find_user_terminals(self,username):
        terminals = None
        if(isinstance(username,str) is True):
            terminal_obj = self.__mongo.find_one({'UserName':username},{'Terminal':1,'_id':0},collection=[self.collection_name,"UserInfo"])
            if(terminal_obj is not None):
                terminals = terminal_obj.get('Terminal',None)
        return terminals

    def update_user_terminals(self,username,terminals):
        result = self.__mongo.update({'UserName':username},{"$set":{"Terminal":terminals}},collection=[self.collection_name,"UserInfo"])
        return result

    def insert_with_time(self,json_obj):
        if(('Owner' in json_obj) and ('Address' in json_obj)):
            json_obj["current_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            return self.__mongo.insert(json_obj,collection=[self.collection_name,json_obj['Owner'],'Terminal',str(json_obj['Address'])])

    def find_latest_one_data(self,username,terminal_address):
        aggregate_command = [{'$sort':{'current_time':pymongo.DESCENDING}},{'$limit':1}]
        result = list(self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username,'Terminal',str(terminal_address)]))
        if(len(result) > 0):
            last_order = result[0]
            if(('_id') in last_order):
                del last_order['_id']
            return last_order
        else:
            return None

    def remove_all(self):
        return self.__mongo.remove({},collection=None)

    def find_one(self):
        return self.__mongo.find_one(collection=None)

    def aggregate_field_area_list(self,username,terminal_address,field_name,limit_length=None):
        time_list = []
        data_list = []
        aggregate_command = [{'$match':{field_name:{'$exists':True}}},{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1,'current_time':1}}]
        if(limit_length is not None):
            aggregate_command[1] = {'$sort':{'current_time':pymongo.DESCENDING}}
            aggregate_command.insert(2,{'$limit':limit_length})
            aggregate_command.insert(3,{'$sort':{'current_time':pymongo.ASCENDING}})
        result = self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username,'Terminal',str(terminal_address)])
        for account in result:
            data_list.append(account.get(field_name))
            time_list.append(account.get('current_time'))
        return data_list,time_list

    def aggregate_field_list(self,username,terminal_address,field_name):
        return self.aggregate_field_area_list(username,terminal_address,field_name,None)

    def aggregate_field_Recent_order_list(self,username,terminal_address,field_name,limit_time):
        time_list = []
        data_list = []
        aggregate_command = [{'$match':{field_name:{'$exists':True}}},{'$match':{'current_time':{'$gt':limit_time}}},{'$sort':{'current_time':pymongo.ASCENDING}},{'$project':{'_id':0,field_name:1,'current_time':1}}]
        result = self.__mongo.aggregate(aggregate_command,collection=[self.collection_name,username,'Terminal',str(terminal_address)])
        for account in result:
            data_list.append(account.get(field_name))
            time_list.append(account.get('current_time'))
        return data_list,time_list


if __name__ == '__main__':
    parameter = {'host':"localhost",'port':27017,'database_name':'IoTSensor','collection_name':'SmartHomeData','user':'root','passwd':'MongoRoot'}
    mongo_conn = SensorMongoORM(**parameter)
    # print(mongo_conn.add_user_info('test_insert',MD5_hash_string('undefault'),[
	# 	{
	# 		"Address":1,
	# 		"Place":"监测点1号位",
	# 		"SensorList":[
	# 			{"SensorType":"LightIntensity","DisplayName":"光照强度","QuantityUnit":"Lux"},
	# 			{"SensorType":"Temperature","DisplayName":"温度" ,"QuantityUnit":"°C"},
	# 			{"SensorType":"Humidity","DisplayName":"湿度" ,"QuantityUnit":"%"},
	# 			{"SensorType":"SmogPercentage","DisplayName":"烟雾浓度" ,"QuantityUnit":"%"},
	# 			{"SensorType":"WaveDistance","DisplayName":"超声波测距" ,"QuantityUnit":"CM"},
	# 			{"SensorType":"BodyStatus","DisplayName":"红外人体监测" ,"QuantityUnit":" "}
	# 		]
	# 	},
	# 	{
	# 		"Address":2,
	# 		"Place":"监测点2号位",
	# 		"SensorList":[
	# 			{"SensorType":"LightIntensity","DisplayName":"光照强度","QuantityUnit":"Lux"},
	# 			{"SensorType":"Temperature","DisplayName":"温度" ,"QuantityUnit":"°C"},
	# 			{"SensorType":"Humidity","DisplayName":"湿度" ,"QuantityUnit":"%"}
	# 		]
	# 	}
	# ]))
    print(dict(mongo_conn.find_latest_one_data('admin',1)))
    # print(mongo_conn.findOne().get('currentime'))











