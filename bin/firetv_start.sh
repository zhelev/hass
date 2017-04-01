#!/bin/sh
docker stop firetv
docker rm firetv
docker run -d -it --name firetv -p 5556:5556 firetv firetv-server -d 192.168.1.167:5555
