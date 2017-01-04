#!/bin/sh
docker ps | grep fire | awk -F "/" '{print $NF}' | awk '{print $NF}'
