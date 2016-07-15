# encoding: utf-8
# all the imports
import eventlet
eventlet.monkey_patch()
import threading
import time
import functools
import re
import datetime
from flask import Flask, jsonify, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing
from ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from DataBaseOperation.SensorMongoORM import SensorMongoORM
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from SensorRecvTCPServer import SensorRecvTCPServerHandler,sensor_recv_TCPserver_run

app = Flask(__name__)
app.config.from_pyfile("flaskr_Configuration.conf")


class IoTSensorWebLauncher(object):
    user_sensor_data_cache = dict()
    mongo_read_conn = None
    socketio = None
    socketio_namespace = "/sensor_socketio"
    socketio_room_set = set()

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
    def get_user_sensor_list_merge(cls,username):
        terminals = IoTSensorWebLauncher.get_user_terminals(username)
        sensor_set = set()
        sensor_list = []
        for terminal in terminals:
            for sensor in terminal["SensorList"]:
                if(sensor["SensorType"] not in sensor_set):
                    sensor_set.add(sensor["SensorType"])
                    sensor_describe = {
                        **sensor,
                        "Location":[{"Address":int(terminal["Address"]),"Place":terminal["Place"]}]
                    }
                    sensor_list.append(sensor_describe)
                else:
                    for sensor_merge in sensor_list:
                        if(sensor_merge["SensorType"] == sensor["SensorType"]):
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
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_list(username,terminal_address,field_name)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def get_today_data_list(cls,username,terminal_address,field_name):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_area_list(username,terminal_address,field_name,300)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def iot_sensor_web_run(cls,application):
        IoTSensorWebLauncher.connect_mongodb()
        if(IoTSensorWebLauncher.socketio is None):
            IoTSensorWebLauncher.socketio = SocketIO(application, async_mode='eventlet')
        SensorRecvTCPServerHandler.add_callback(IoTSensorWebLauncher.send_socketio)
        sensor_recv_TCPserver_run()
        print('read_sensorDB_thread started!')
        print(application.config["DEBUG"],application.config["FLASKR_HOST"],application.config["FLASKR_PORT"])
        IoTSensorWebLauncher.socketio.run(application, host = application.config["FLASKR_HOST"], port = application.config["FLASKR_PORT"], debug = application.config["DEBUG"])


def judge_is_logged_for_get_page(function):
    @functools.wraps(function)
    def decorated_fun(*args,**kwargs):
        if(session.get('logged_in', None) is not True):
            return redirect(url_for('login'))
        elif(session.get('logged_in', None) is True):
            return function(*args,**kwargs)
    return decorated_fun

def judge_is_logged_for_get_data(function):
    @functools.wraps(function)
    def decorated_fun(*args,**kwargs):
        if(session.get('logged_in', None) is not True):
            return jsonify(None)
        elif(session.get('logged_in', None) is True):
            return jsonify(function(*args,**kwargs))
    return decorated_fun

IoTSensorWebLauncher.creat_socketio(app)

@app.route('/')
@judge_is_logged_for_get_page
def root_route():
    return redirect(url_for('main_frame_show'))


@app.errorhandler(404)
@app.route('/404_error')
def page_not_found(error):
    return render_template('404_error_files.html'), 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if session.get('logged_in'):
        return redirect(url_for('sensor'))
    if request.method == 'POST':
        user_seached_password = IoTSensorWebLauncher.get_user_password(request.form['username'])
        if(user_seached_password is None):
            error = 'Invalid username!'
        elif request.form['password'] != user_seached_password:
            error = 'Invalid password!'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            return redirect(url_for('main_frame_show'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/main')
@judge_is_logged_for_get_page
def main_frame_show():
    return render_template('main_frame.html', username = session.get('username'))

@app.route('/user_info')
@judge_is_logged_for_get_page
def user_info_show():
    username = session.get('username')
    return render_template('user_info.html', username = username, terminals = IoTSensorWebLauncher.get_user_terminals(username))

@app.route('/lightControl')
@judge_is_logged_for_get_page
def lights_control():
    return render_template('light_control.html')


@app.route('/Sensor')
@judge_is_logged_for_get_page
def sensor():
    return render_template('Sensor.html')


@app.route('/getSensorData')
@judge_is_logged_for_get_data
def sensor_data():
    return IoTSensorWebLauncher.user_sensor_data_cache.get(session.get('username', None),None)

@app.route('/getHistoryDataChart')
@judge_is_logged_for_get_page
def get_history_data_chart():
    sensor_list = IoTSensorWebLauncher.get_user_sensor_list_merge(session.get('username', None))
    return render_template('history_data_chart.html',sensor_list = sensor_list)

@app.route('/getHistoryData')
@judge_is_logged_for_get_data
def get_history_data():
    username = session.get('username', None)
    terminal_address = request.args.get('address')
    sensor_type = request.args.get('type')
    return IoTSensorWebLauncher.get_history_data_list(username, terminal_address, sensor_type)

@app.route('/getTodayDataChart')
@judge_is_logged_for_get_page
def get_today_data_chart():
    sensor_list = IoTSensorWebLauncher.get_user_sensor_list_merge(session.get('username', None))
    return render_template('today_data_chart.html',sensor_list = sensor_list)

@app.route('/getTodayData')
@judge_is_logged_for_get_data
def get_today_data():
    return IoTSensorWebLauncher.get_today_data_list(session.get('username', None),request.args.get('address'),request.args.get('type'))


@IoTSensorWebLauncher.socketio.on('connect',namespace=IoTSensorWebLauncher.socketio_namespace)
def socketio_connect_handler():
    if(session.get('logged_in', None) is not True):
        return False
    elif(session.get('logged_in', None) is True):
        print(request.sid + ' is connecting...')
        room = session.get('username', None)
        if room is not None:
            join_room(room)
            IoTSensorWebLauncher.socketio_room_set.add(room)
            print(request.sid + ' is join room...')


@IoTSensorWebLauncher.socketio.on('disconnect',namespace=IoTSensorWebLauncher.socketio_namespace)
def socketio_disconnect_handler():
    room = session.get('username', None)
    rooms = IoTSensorWebLauncher.socketio.server.manager.rooms
    namesapce = IoTSensorWebLauncher.socketio_namespace
    print(request.sid + ' is disconnecting...')
    leave_room(room)
    if(((namesapce in rooms) and (room in rooms.get(namesapce))) is False):
        IoTSensorWebLauncher.socketio_room_set.discard(room)

if __name__ == '__main__':
    IoTSensorWebLauncher.iot_sensor_web_run(app)










