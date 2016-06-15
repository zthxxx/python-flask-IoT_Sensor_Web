# encoding: utf-8
# all the imports
import threading
import time
import functools
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
                IoTSensorWebLauncher.sensor_json = dict(IoTSensorWebLauncher.mongo_read_conn.findLatestOne())
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
    def iot_sensor_web_run(cls):
        IoTSensorWebLauncher.connect_mongodb()
        read_sensorDB_thread = threading.Thread(target=IoTSensorWebLauncher.loop_read_sensorDB_data)
        read_sensorDB_thread.start()
        print('read_sensorDB_thread started!')
        app.debug = app.config["DEBUG"]
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if session.get('logged_in'):
        return redirect(url_for('sensor'))
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            return redirect(url_for('sensor'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/main')
@judgeIsLogged
def main_frame_show():
    return render_template('main_frame.html', username = session.get('username'))


@app.route('/Sensor')
@judgeIsLogged
def sensor():
    return render_template('Sensor.html')


@app.route('/SensorData')
def sensor_data():
    if(session.get('logged_in', None) is not True):
            return jsonify(None)
    elif(session.get('logged_in', None) is True):
            return jsonify(**IoTSensorWebLauncher.sensor_json)

if __name__ == '__main__':
    IoTSensorWebLauncher.iot_sensor_web_run()



