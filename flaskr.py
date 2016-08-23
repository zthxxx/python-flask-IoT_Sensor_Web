# encoding: utf-8
# all the imports
import eventlet
eventlet.monkey_patch()
import functools
import json
from flask import Flask, jsonify, request, session, g, redirect, url_for, abort, render_template, flash
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from IoTSensorWebLauncher import IoTSensorWebLauncher
from HashTools.MD5Tools import MD5_hash_string
from SensorRecvTCPServer import SensorRecvTCPServerHandler
from TianMaoProtocol.TianMaoProtocol import AssembleCommunicationProtocolPacket

app = Flask(__name__)
app.config.from_pyfile("flaskr_Configuration.conf")

def judge_is_logged_for_get_page(function):
    @functools.wraps(function)
    def decorated_fun(*args,**kwargs):
        if session.get('logged_in', None) is not True:
            return redirect(url_for('login'))
        elif session.get('logged_in', None) is True:
            return function(*args,**kwargs)
    return decorated_fun

def judge_is_logged_for_get_data(function):
    @functools.wraps(function)
    def decorated_fun(*args,**kwargs):
        if session.get('logged_in', None) is not True:
            return jsonify(None)
        elif session.get('logged_in', None) is True:
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
        if user_seached_password is None:
            error = 'Invalid username!'
        elif request.form['password'] != user_seached_password:
            error = 'Invalid password!'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            session.permanent = True
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

@app.route('/user_info_alter', methods=['GET', 'POST'])
@judge_is_logged_for_get_data
def user_info_alter():
    user_info = json.loads(request.form.get('user_info'))
    username = session.get('username')
    if username != user_info.get("UserName"):
        return None
    if "InitPassword" in user_info:
        user_seached_password = IoTSensorWebLauncher.get_user_password(username)
        if (user_seached_password is None) or (user_info.get("InitPassword") != user_seached_password) or ("NewPassword" not in user_info):
            return None
        IoTSensorWebLauncher.update_user_password(username,user_info.get("NewPassword"))
    terminals = user_info.get("Terminal")
    if terminals is not None:
        IoTSensorWebLauncher.filter_save_terminals(username,terminals)
        return "Success"
    return None

@app.route('/ObjectControl')
@judge_is_logged_for_get_page
def object_control():
    terminals_list = IoTSensorWebLauncher.get_user_terminals(session.get('username', None))
    return render_template('light_control.html', terminals_list = terminals_list)

@app.route('/SwitchValueTurn', methods=['POST'])
@judge_is_logged_for_get_data
def switch_value_turn():
    username = session.get('username')
    terminal_address = request.form.get('terminal_address')
    switch_type = request.form.get('switch_type')
    switch_index = request.form.get('switch_index')
    switch_status = request.form.get('switch_status')
    message = {
        "InfoType": "Setting",
        "Owner":username,
        "Address":int(terminal_address),
        "SwitchSet":{
            "SwitchType":str(switch_type),
            "SwitchIndex":int(switch_index),
            "StatusSet":int(switch_status)
        }
    }
    print(message)
    IoTSensorWebLauncher.send_terminal_json_message(username, terminal_address, "FunctionWord_SetProperty", message)
    return "Success"

@app.route('/videoChat')
@judge_is_logged_for_get_page
def video_chat():
    username = session.get('username')
    skyrtc_server_port = IoTSensorWebLauncher.skyRTC_config.get('port')
    return render_template('videoChat.html',room = MD5_hash_string(username),skyrtc_server_port = skyrtc_server_port)

@app.route('/Sensor')
@judge_is_logged_for_get_page
def sensor():
    terminals_list = IoTSensorWebLauncher.get_user_terminals(session.get('username', None))
    return render_template('Sensor.html',terminals_list = terminals_list)

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
    if session.get('logged_in', None) is not True:
        return False
    elif session.get('logged_in', None) is True:
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
    if ((namesapce in rooms) and (room in rooms.get(namesapce))) is False:
        IoTSensorWebLauncher.socketio_room_set.discard(room)

if __name__ == '__main__':
    IoTSensorWebLauncher.iot_sensor_web_run(app)










