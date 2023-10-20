# -*- coding: utf-8 -*-
import gevent.monkey

from config import job_server_port

gevent.monkey.patch_all()  # gevent的猴子魔法 变成非阻塞

bind = f'0.0.0.0:{job_server_port}'  # 访问地址

workers = 1  # 启动的进程数
worker_class = 'gevent'  # 使用gevent模式，还可以使用sync 模式，默认的是sync模式
threads = 20  # 每个进程开启的线程数
x_forwarded_for_header = 'X_FORWARDED-FOR'
