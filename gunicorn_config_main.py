# -*- coding: utf-8 -*-
import gevent.monkey

gevent.monkey.patch_all(select=False)  # gevent的猴子魔法 变成非阻塞
import multiprocessing

from config import _main_server_port

bind = f'0.0.0.0:{_main_server_port}'  # 访问地址

workers = multiprocessing.cpu_count() * 2 + 1  # 启动的进程数，cpu个数 * 2 + 1
worker_class = 'gevent'  # 使用gevent模式，还可以使用sync 模式，默认的是sync模式
threads = 20  # 每个进程开启的线程数
x_forwarded_for_header = 'X_FORWARDED-FOR'
