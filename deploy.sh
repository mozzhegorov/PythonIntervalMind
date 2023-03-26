docker stop pythonmind
docker rm pythonmind
docker build -t pythonmind .
docker run -v /home/pi/Projects/PythonIntervalMind/db:/home/db -v /home/pi/Projects/RaspberryAdmin/raspberryadmin/mediafiles/:/home/media --name pythonmind -d --restart unless-stopped pythonmind
