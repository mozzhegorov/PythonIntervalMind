docker stop pythonmind
docker rm pythonmind
docker build -t pythonmind .
docker run -v /home/pi/Projects/PythonIntervalMind/db:/home/db --name pythonmind -d --restart unless-stopped pythonmind
