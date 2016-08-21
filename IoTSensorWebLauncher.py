# encoding: utf-8
# all the imports
import re
import json
from ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from DataBaseOperation.SensorMongoORM import SensorMongoORM
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from SensorRecvTCPServer import SensorRecvTCPServerHandler,sensor_recv_TCPserver_run


class IoTSensorWebLauncher(object):
    user_sensor_data_cache = dict()
    mongo_read_conn = None
    socketio = None
    socketio_namespace = "/sensor_socketio"
    socketio_room_set = set()
    skyRTC_config = dict()

    @classmethod
    def creat_socketio(cls,application):
        '''
        :param application:
        :return: None
        This method should be called before "@IoTSensorWebLauncher.socketio.on",better practice is called it before @app
        '''
        IoTSensorWebLauncher.socketio = SocketIO(application, async_mode='eventlet')

    @classmethod
    def connect_mongodb(cls):
        initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
        databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
        databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
        IoTSensorWebLauncher.mongo_read_conn = SensorMongoORM(**databaseConnectConfig)

    @classmethod
    def get_SkyRtcServerConfig(cls):
        initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
        databaseConnectConfig = initializationConfigParser.GetAllNodeItems("SkyRtcWebsocketServer")
        config_path = databaseConnectConfig.get("config_path")
        IoTSensorWebLauncher.skyRTC_config = json.load(open(config_path, 'r'))

    @classmethod
    def send_socketio(cls,data):
        IoTSensorWebLauncher.user_sensor_data_cache[data.get('Owner')] = data
        IoTSensorWebLauncher.socketio.emit('sensor_socketio_data',data, namespace=IoTSensorWebLauncher.socketio_namespace,room=data.get('Owner'))

    @classmethod
    def ParameterDecorate(cls,function,*args,**kwargs):
        @classmethod
        def Decorated(cls):
            return function(*args,**kwargs)
        return Decorated

    @classmethod
    def get_user_password(cls,username):
        username_filtered = re.sub('[^a-zA-Z0-9_]',"",username)
        password = IoTSensorWebLauncher.mongo_read_conn.find_user_password(username_filtered)
        return password

    @classmethod
    def get_user_terminals(cls,username):
        username_filtered = re.sub('[^a-zA-Z0-9_]',"",username)
        terminal_list = IoTSensorWebLauncher.mongo_read_conn.find_user_terminals(username_filtered)
        return terminal_list

    @classmethod
    def update_user_terminals(cls,username,terminals):
        username_filtered = re.sub('[^a-zA-Z0-9_]',"",username)
        IoTSensorWebLauncher.mongo_read_conn.update_user_terminals(username_filtered,terminals)

    @classmethod
    def filter_save_terminals(cls,username,terminals):
        username_filtered = re.sub('[^a-zA-Z0-9_]',"",username)
        IoTSensorWebLauncher.mongo_read_conn.filter_save_terminals(username_filtered,terminals)

    @classmethod
    def update_user_password(cls,username,password):
        username_filtered = re.sub('[^a-zA-Z0-9_]',"",username)
        IoTSensorWebLauncher.mongo_read_conn.update_user_password(username_filtered,password)

    @classmethod
    def get_user_sensor_list_merge(cls,username):
        terminals = IoTSensorWebLauncher.get_user_terminals(username)
        sensor_set = set()
        sensor_list = []
        for terminal in terminals:
            for sensor in terminal["SensorList"]:
                if sensor["SensorType"] not in sensor_set:
                    sensor_set.add(sensor["SensorType"])
                    sensor_describe = {
                        **sensor,
                        "Location":[{"Address":int(terminal["Address"]),"Place":terminal["Place"]}]
                    }
                    sensor_list.append(sensor_describe)
                else:
                    for sensor_merge in sensor_list:
                        if sensor_merge["SensorType"] == sensor["SensorType"]:
                            location_describe = {"Address":int(terminal["Address"]),"Place":terminal["Place"]}
                            sensor_merge["Location"].append(location_describe)
                            break
        return sensor_list

    @classmethod
    def get_latest_one_data(cls,username,terminal_address):
        last_older = IoTSensorWebLauncher.mongo_read_conn.find_latest_one_data(username,terminal_address)
        return last_older

    @classmethod
    def get_history_data_list(cls,username,terminal_address,field_name):
        data_list,time_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_list(username,terminal_address,field_name)
        data_dict = {'sensor_type':field_name,"data":data_list,"time":time_list}
        return data_dict

    @classmethod
    def get_today_data_list(cls,username,terminal_address,field_name):
        data_list,time_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_area_list(username,terminal_address,field_name,300)
        data_dict = {'sensor_type':field_name,"data":data_list,"time":time_list}
        return data_dict

    @classmethod
    def iot_sensor_web_run(cls,application):
        IoTSensorWebLauncher.connect_mongodb()
        IoTSensorWebLauncher.get_SkyRtcServerConfig()
        if IoTSensorWebLauncher.socketio is None:
            IoTSensorWebLauncher.socketio = SocketIO(application, async_mode='eventlet')
        SensorRecvTCPServerHandler.add_callback(IoTSensorWebLauncher.send_socketio)
        sensor_recv_TCPserver_run()
        print('read_sensorDB_thread started!')
        print(application.config["DEBUG"],application.config["FLASKR_HOST"],application.config["FLASKR_PORT"])
        IoTSensorWebLauncher.socketio.run(application, host = application.config["FLASKR_HOST"], port = application.config["FLASKR_PORT"], debug = application.config["DEBUG"])

