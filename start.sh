#!/bin/bash

nohup python3 /usr/local/python3/bin/gunicorn -c gunicorn_config_main.py main:app &
echo "主应用启动完成"

nohup python3 /usr/local/python3/bin/gunicorn -c gunicorn_config_job.py job:job &
echo "任务调度应用启动完成"
