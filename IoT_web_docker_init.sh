#!/bin/bash
#Docker image from ubuntu version >= 14.04
#Docker image run command example:
#:~$ wget https://raw.githubusercontent.com/zthxxx/python-flask-IoT_Sensor_Web/feature/IoT_web_docker_init.sh
#:~$ docker run -dit -v /var/database/mongodb:/var/database/mongodb -p 80:80 -p 31511:31511 -p 3000:3000 ubuntu /bin/bash
#:~$ cat IoT_web_docker_init.sh | docker exec -i $(docker ps -q) tee /root/IoT_web_docker_init.sh
#:~$ docker exec -t $(docker ps -q) chmod +x /root/IoT_web_docker_init.sh; /root/IoT_web_docker_init.sh | tee -a /root/docker_init.log

apt-get update
yes | apt-get install wget
yes | apt-get install vim
echo '
set number
set relativenumber
filetype on
set history=1000
set background=dark
syntax on
set autoindent
set smartindent
set tabstop=4
set shiftwidth=4
set showmatch
set ruler
set nowrap
set textwidth=0
set hlsearch
' | tee ~/.vimrc

########## python3.5 setup
yes | apt-get install python3.5
yes | apt-get install python3.5-dev
cd ~
wget https://bootstrap.pypa.io/ez_setup.py
python3.5 ez_setup.py
easy_install-3.5 pip
rm -rf ez_setup.py setuptools-*.zip

########## git setup
yes | apt-get install git
git config --global user.name "tian_ubuntu_docker"
git config --global user.email "zth_9451@qq.com"
rm -rf ~/.ssh/
echo | ssh-keygen -t rsa -q -P '' -C "zth_9451@qq.com"
eval `ssh-agent`
ssh-add ~/.ssh/id_rsa

########## mongodb setup
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list
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
yes | apt-get install nodejs
yes | apt-get install npm

######### flask web pull
PROJECT_NAME="Project/Python/FlaskProject"
cd ~
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME
wget https://github.com/zthxxx/python-flask-IoT_Sensor_Web/archive/feature.zip -O python-flask-IoT_Sensor_Web.zip
yes | apt-get install unzip
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






