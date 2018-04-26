#!/bin/bash

# plz see usage in README


apt update
apt install -y wget vim
wget -q git.io/tvimrc -O ~/.vimrc

########## python3.5 setup
apt install -y python3.5 python3.5-dev
cd ~
wget https://bootstrap.pypa.io/ez_setup.py
python3.5 ez_setup.py
easy_install-3.5 pip
rm -rf ez_setup.py setuptools-*.zip

########## git setup
apt-get install git
git config --global user.name "tian_ubuntu_docker"
git config --global user.email "zth_9451@qq.com"
rm -rf ~/.ssh/
echo | ssh-keygen -t rsa -q -P '' -C "zth_9451@qq.com"
eval `ssh-agent`
ssh-add ~/.ssh/id_rsa

########## mongodb setup
# mirror ref: https://mirror.tuna.tsinghua.edu.cn/help/mongodb/
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb https://mirrors.tuna.tsinghua.edu.cn/mongodb/apt/ubuntu trusty/mongodb-org/stable multiverse" | tee /etc/apt/sources.list.d/mongodb.list
apt-get update
apt-get install -y mongodb-org

MONGO_PATH="/var/database/mongodb"
mkdir -p $MONGO_PATH/db
mkdir -p $MONGO_PATH/log
echo "
# /etc/mongodb.conf
dbpath=$MONGO_PATH/db
logpath=$MONGO_PATH/log/mongodb.log
logappend=true
bind_ip = 127.0.0.1
port = 27017
storageEngine = wiredTiger
" | tee /etc/mongodb.conf
mongod --config /etc/mongodb.conf &
echo '
use admin
db.createUser({"user":"root","pwd":"MongoRoot","roles":[{role:"root",db:"admin"},{role:"readWrite",db:"admin"},{role:"readWrite",db:"IoTSensor"}]})
db.shutdownServer()
exit
' | mongo
echo 'auth = true' >> /etc/mongodb.conf
mongod --config /etc/mongodb.conf &

######### nodejs & npm
apt-get install nodejs npm

######### flask web pull
PROJECT_NAME="Project/Python/FlaskProject"
cd ~
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME
wget https://github.com/zthxxx/python-flask-IoT_Sensor_Web/archive/feature.zip -O python-flask-IoT_Sensor_Web.zip
apt-get install unzip
unzip python-flask-IoT_Sensor_Web.zip
rm -f python-flask-IoT_Sensor_Web.zip
mv python-flask-IoT_Sensor_Web-feature python-flask-IoT_Sensor_Web
cd python-flask-IoT_Sensor_Web
python3.5 -m pip install -r requirements.txt
cd skyRTC_Node_Server
npm install
cd ..
perl -p -i -e "s/sudo //g" IoT_Web_Server_Restart.sh
echo '

#############  The next step need config files.  #############

'
#The next step need config files
#./IoT_Web_Server_Restart.sh






