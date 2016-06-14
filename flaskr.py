# all the imports
import sqlite3
from flask import Flask, jsonify, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from  ConfigFileInfoParser.InitializationConfigParser import InitializationConfigParser
from ServerClientSocket.ProcessingQueueNode import ProcessingQueueNode


app = Flask(__name__)
app.config.from_pyfile("flaskr_Configuration.conf")
sensor_json = dict()

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
        jsonData = queueNode.GetTaskQueuePop()
        if(jsonData is not None):
            sensor_json = jsonData
        return jsonify(**sensor_json)
    else:
        return jsonify(None)



if __name__ == '__main__':
    initializationConfigParser = InitializationConfigParser("ServerConfig.ini")
    serverConnectConfig = initializationConfigParser.GetAllNodeItems("ServerSocket")
    serverConnectConfig["port"] = int(serverConnectConfig.get("port"))
    queueNode = ProcessingQueueNode()
    queueNode.StartConnect(**serverConnectConfig)

    app.debug = app.config["DEBUG"]
    print("OK")

    app.run(host = "0.0.0.0",port = 80)




