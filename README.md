# IoT Sensor Web

A demo flask server for IoT sensor manager. 

See demo on [https://iot.zthxxx.me](https://iot.zthxxx.me)

Platform: Ubuntu 14.04



## Architecture 

```
Docker
  |__ MongoDB
  
Docker
  |__ Flask
  |__ SkyRTC
```

![Architecture](./Documents/Architecture.png)

## Install

**! Make sure U have docker**

```bash
cd ~/Download
wget https://raw.githubusercontent.com/zthxxx/python-flask-IoT_Sensor_Web/feature/IoT_web_docker_init.sh
docker run -dit --name IoT -v /var/database/mongodb:/var/database/mongodb -p 80:80 -p 31511:31511 -p 3000:3000 ubuntu:16.04 /bin/bash
cat IoT_web_docker_init.sh | docker exec -i IoT tee /root/IoT_web_docker_init.sh
docker exec IoT chmod +x /root/IoT_web_docker_init.sh
docker exec IoT /root/IoT_web_docker_init.sh | docker exec -i IoT tee -a /root/docker_init.log
```



## Start

Then should **EDIT** the config file `flaskr_Configuration.conf` and `ServerConfig.ini`

```bash
docker exec -it IoT bash
wget -q git.io/tvimrc -O ~/.vimrc
cd ~/Project/Python/FlaskProject/python-flask-IoT_Sensor_Web
cp flaskr_Configuration.conf.example flaskr_Configuration.conf
cp ServerConfig.ini.example ServerConfig.ini
vim flaskr_Configuration.conf
vim ServerConfig.ini
./IoT_Web_Server_Restart.sh
```



## License

GPL
