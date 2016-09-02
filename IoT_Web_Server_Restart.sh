#!/bin/bash

echo_colorful(){
	for var in "$@"
	do
		case "$var" in
			-black)
				echo -ne "\033[30;1m";
			;;
			-red)
				echo -ne "\033[31;1m";
			;;
			-green)
				echo -ne "\033[32;1m";
			;;
			-yellow)
				echo -ne "\033[33;1m";
			;;
			-blue)
				echo -ne "\033[34;1m";
			;;
			-purple)
				echo -ne "\033[35;1m";
			;;
			-cyan)
				echo -ne "\033[36;1m";
			;;
			-white|-gray) 
				echo -ne "\033[37;1m";
			;;
			 -h|-help|--help)
			 	echo "Usage: echo_coloful -color1 message1 -color2 message2 ...";
				echo "eg:		echo_colorul -red message_1 [ -blue message2 ]";
				return 0
			;;
			*)
				echo -ne "$var"
			;;
		esac
	done
	echo -e "\033[0m";
}

kill_proceeding(){
	process_names=$@
	for process_name in $process_names
	do
		process_pid=$(sudo pidof $process_name)
		if [ "$process_pid" ];then 
			sudo kill -9 $process_pid
			echo_colorful -yellow "${process_name} is running, now kill and restart it."
		else 
			echo_colorful -red "${process_name} is NOT run."
		fi
	done
	return 0
}

exist_command_process(){
	if [ $# == 0 ];then
		return 1
	fi
	process_pid=$(sudo ps -ax | grep -wE "${1}$" | grep -v grep | grep -oE '^ *[0-9]* ')
	if [ "$process_pid" ];then 
		return 0
	else 
		return 1
	fi
}

kill_command(){ 
	for process_command in "$@"
	do
		process_pid=$(sudo ps -ax | grep -wE "${process_command}$" | grep -v grep | grep -oE '^ *[0-9]* ')
		if [ "$process_pid" ];then 
			sudo kill -9 $process_pid
			echo_colorful -green "${process_command}" -yellow " is running, now kill it."
		else 
			echo_colorful -green "${process_command}" -red " is NOT run."
		fi
	done
	return 0
}

sudo echo
echo_colorful -yellow "

==================================================
          IoT_Sensor_Web script init...
"

mongod_command='mongod --storageEngine wiredTiger --auth'
IoT_web_py='flaskr.py'
IoT_web_command="python3.5 ${IoT_web_py}"
IoT_web_default_folder='/home/ubuntu/Project/Python/FlaskProject/python-flask-IoT_Sensor_Web/'
skyrtc_server_command='nodejs skyrtc_server.js'

kill_command "$IoT_web_command" 

exist_command_process "$mongod_command"
if [ $? != 0 ];then
	sudo $mongod_command &
	echo_colorful -yellow "start mongodb"
fi

if [ ! -f "$IoT_web_py" ];then
	cd "$IoT_web_default_folder"
	if [ $? != 0 -o ! -f "$IoT_web_py" ];then
		echo_colorful -red  "$IoT_web_py is NOT exist!"
		exit 0
	fi
fi

if [ "$1" == "-up" ];then
	echo_colorful -yellow "Git pull update data..."
	git pull origin feature
	if [ $? != 0 ];then
		echo_colorful -red "Git is not ready!"
		exit 0
	fi
fi

rm web_log.log
nohup sudo $IoT_web_command >web_log.log 2>&1 &
echo_colorful -yellow "start python"

cd skyRTC_Node_Server/
exist_command_process "$skyrtc_server_command"
if [ $? != 0 ];then
	rm skyrtc_log.log
	nohup sudo $skyrtc_server_command >skyrtc_log.log 2>&1 &
	echo_colorful -yellow "start nodejs"
fi


echo_colorful -yellow " 

==================================================
           IoT_Sensor_Web is running!

"
