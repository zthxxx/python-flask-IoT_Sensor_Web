# encoding: utf-8
# all the imports
import threading
import time
import functools
import datetime
from flask import Flask, jsonify, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from  ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from DataBaseOperation.SensorMongoORM import SensorMongoORM

app = Flask(__name__)
app.config.from_pyfile("flaskr_Configuration.conf")


class IoTSensorWebLauncher(object):
    sensor_json = dict()
    mongo_read_conn = None

    @classmethod
    def connect_mongodb(cls):
        initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
        databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
        databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
        IoTSensorWebLauncher.mongo_read_conn = SensorMongoORM(**databaseConnectConfig)

    @classmethod
    def loop_read_sensorDB_data(cls):
        while(True):
            if(isinstance(IoTSensorWebLauncher.mongo_read_conn,SensorMongoORM)):
                latest_one = IoTSensorWebLauncher.mongo_read_conn.findLatestOne()
                if(latest_one is not None):
                    IoTSensorWebLauncher.sensor_json = latest_one
                    if(IoTSensorWebLauncher.sensor_json.has_key("current_time")):
                        del IoTSensorWebLauncher.sensor_json["current_time"]
                    time.sleep(1)

    @classmethod
    def ParameterDecorate(cls,function,*args,**kwargs):
        @classmethod
        def Decorated(cls):
            return function(*args,**kwargs)
        return Decorated

    @classmethod
    def get_history_data_list(cls,field_name):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregateFieldToList(field_name)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def get_today_data_list(cls,field_name):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregateFieldToAreaList(field_name,300)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def get_last_order_data(cls,field_name,limit_time):
        data_list = IoTSensorWebLauncher.mongo_read_conn.aggregateFieldRecentOrderList(field_name,limit_time)
        data_dict = {'sensor_type':field_name,"data":data_list}
        return data_dict

    @classmethod
    def iot_sensor_web_run(cls):
        IoTSensorWebLauncher.connect_mongodb()
        read_sensorDB_thread = threading.Thread(target=IoTSensorWebLauncher.loop_read_sensorDB_data)
        read_sensorDB_thread.start()
        print('read_sensorDB_thread started!')
        app.debug = app.config["DEBUG"]
        print(app.config["DEBUG"],app.config["FLASKR_HOST"],app.config["FLASKR_PORT"])
        app.run(host = app.config["FLASKR_HOST"],port = app.config["FLASKR_PORT"])



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
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username!'
        elif request.form['password'] != app.config['PASSWORD']:
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
        # print(IoTSensorWebLauncher.sensor_json.get(request.args.get('type')))
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
            return jsonify(IoTSensorWebLauncher.get_history_data_list(request.args.get('type')))

@app.route('/getTodayDataChart')
@judgeIsLogged
def get_today_data_chart():
    return render_template('today_data_chart.html')

@app.route('/getTodayData')
def get_today_data():
    if(session.get('logged_in', None) is not True):
        return jsonify(None)
    elif(session.get('logged_in', None) is True):
        return jsonify(IoTSensorWebLauncher.get_today_data_list(request.args.get('type')))


@app.route('/getLastOrderData')
def get_LastOrder_data():
    if(session.get('logged_in', None) is not True):
        return jsonify(None)
    elif(session.get('logged_in', None) is True):
        thirty_seconds_before = (datetime.datetime.now() - datetime.timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(IoTSensorWebLauncher.get_last_order_data(request.args.get('type'), thirty_seconds_before))


if __name__ == '__main__':
    IoTSensorWebLauncher.iot_sensor_web_run()










