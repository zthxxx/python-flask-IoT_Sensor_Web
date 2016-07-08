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
    sensor_json = dict()
    mongo_read_conn = None
    socketio = SocketIO(app, async_mode='eventlet')
    socketio_namespace = "/sensor_socketio"
    socketio_room_set = set()

    @classmethod
    def connect_mongodb(cls):
        initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
        databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
        databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
        IoTSensorWebLauncher.mongo_read_conn = SensorMongoORM(**databaseConnectConfig)

    @classmethod
    def send_socketio(cls,data):
            IoTSensorWebLauncher.socketio.emit('sensor_socketio_data',data, namespace=IoTSensorWebLauncher.socketio_namespace,room=data.get('Owner'))

    @classmethod
    def ParameterDecorate(cls,function,*args,**kwargs):
        @classmethod
        def Decorated(cls):
            return function(*args,**kwargs)
        return Decorated
    
    @classmethod
    def get_user_password(cls,username):
        username_filter = re.sub('[^a-zA-Z0-9_]',"",username)
        password = IoTSensorWebLauncher.mongo_read_conn.find_user_password(username_filter)
        return password
        
    @classmethod
    def get_history_data_list(cls,username,field_name):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_list(username,field_name)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def get_today_data_list(cls,username,field_name):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregate_field_area_list(username,field_name,300)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def iot_sensor_web_run(cls):
        global app
        IoTSensorWebLauncher.connect_mongodb()
        SensorRecvTCPServerHandler.add_callback(IoTSensorWebLauncher.send_socketio)
        sensor_recv_TCPserver_run()
        print('read_sensorDB_thread started!')
        print(app.config["DEBUG"],app.config["FLASKR_HOST"],app.config["FLASKR_PORT"])
        IoTSensorWebLauncher.socketio.run(app, host = app.config["FLASKR_HOST"], port = app.config["FLASKR_PORT"], debug = app.config["DEBUG"])


def judgeIsLogged(function):
    @functools.wraps(function)
    def decorated_fun(*args,**kwargs):
        if(session.get('logged_in', None) is not True):
            return redirect(url_for('login'))
        elif(session.get('logged_in', None) is True):
            return function(*args,**kwargs)
    return decorated_fun


@app.route('/')
@judgeIsLogged
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
@judgeIsLogged
def main_frame_show():
    return render_template('main_frame.html', username = session.get('username'))

@app.route('/lightControl')
@judgeIsLogged
def lights_control():
    return render_template('light_control.html')


@app.route('/Sensor')
@judgeIsLogged
def sensor():
    return render_template('Sensor.html')


@app.route('/getSensorData')
def sensor_data():
    if(session.get('logged_in', None) is not True):
        return jsonify(None)
    elif(session.get('logged_in', None) is True):
        return jsonify(IoTSensorWebLauncher.sensor_json)

@app.route('/getHistoryDataChart')
@judgeIsLogged
def get_history_data_chart():
    return render_template('history_data_chart.html')

@app.route('/getHistoryData')
def get_history_data():
    if(session.get('logged_in', None) is not True):
            return jsonify(None)
    elif(session.get('logged_in', None) is True):
            return jsonify(IoTSensorWebLauncher.get_history_data_list(session.get('username', None),request.args.get('type')))

@app.route('/getTodayDataChart')
@judgeIsLogged
def get_today_data_chart():
    return render_template('today_data_chart.html')

@app.route('/getTodayData')
def get_today_data():
    if(session.get('logged_in', None) is not True):
        return jsonify(None)
    elif(session.get('logged_in', None) is True):
        return jsonify(IoTSensorWebLauncher.get_today_data_list(session.get('username', None),request.args.get('type')))


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
    IoTSensorWebLauncher.iot_sensor_web_run()










