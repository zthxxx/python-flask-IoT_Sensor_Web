# encoding: utf-8
# all the imports
import threading
import time
from flask import Flask, jsonify, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from  ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from DataBaseOperation.SensorMongoORM import SensorMongoORM

app = Flask(__name__)
app.config.from_pyfile("flaskr_Configuration.conf")
sensor_json = dict()
mongo_read_conn = None

@app.route('/')
def root_route():
    if session.get('logged_in'):
        return redirect(url_for('sensor'))
    else:
        return redirect(url_for('login'))


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
    return redirect(url_for('root_route'))

@app.route('/main')
def main_frame_show():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main_frame.html', username = session.get('username'))


@app.route('/Sensor')
def sensor():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('Sensor.html')

@app.route('/SensorData')
def sensor_data():
    global sensor_json
    if session.get('logged_in'):
        return jsonify(**sensor_json)
    else:
        return jsonify(None)

def connect_mongodb():
    global mongo_read_conn
    initializationConfigParser = InitializationConfigParser("ServerConfig.ini")

    databaseConnectConfig = initializationConfigParser.GetAllNodeItems("DataBase")
    databaseConnectConfig["port"] = int(databaseConnectConfig.get("port"))
    mongo_read_conn = SensorMongoORM(**databaseConnectConfig)

def loop_read_sensorDB_data():
    global mongo_read_conn
    global sensor_json
    while(True):
        if(isinstance(mongo_read_conn,SensorMongoORM)):
            sensor_json = dict(mongo_read_conn.findLatestOne())
            if(sensor_json.has_key("current_time")):
                del sensor_json["current_time"]
            time.sleep(1)

def ParameterDecorate(function,*args,**kwargs):
    def Decorated():
        return function(*args,**kwargs)
    return Decorated

def iot_sensor_web_run():
    connect_mongodb()

    # threads = []
    read_sensorDB_thread = threading.Thread(target=loop_read_sensorDB_data)
    # threads.append(read_sensorDB_thread)
    # iot_sensor_web_thread = threading.Thread(target=ParameterDecorate(app.run,**{'host':app.config["FLASKR_HOST"],'port':app.config["FLASKR_PORT"]}))
    # threads.append(iot_sensor_web_thread)
    # for threadline in threads:
    #     threadline.start()
    read_sensorDB_thread.start()
    print('read_sensorDB_thread started!')
    app.debug = app.config["DEBUG"]
    app.run(host = app.config["FLASKR_HOST"],port = app.config["FLASKR_PORT"])


if __name__ == '__main__':
    iot_sensor_web_run()



