#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : gunicornConfig.py
# @Software: PyCharm

import gevent.monkey
import multiprocessing

"""
gunicorn的配置文件
"""

gevent.monkey.patch_all()  # gevent的猴子魔法 变成非阻塞

bind = '0.0.0.0:8024'  # 访问地址

workers = multiprocessing.cpu_count() * 2 + 1  # 启动的进程数，cpu个数 * 2 + 1
worker_class = 'gevent'  # 使用gevent模式，还可以使用sync 模式，默认的是sync模式
threads = 20  # 每个进程开启的线程数
x_forwarded_for_header = 'X_FORWARDED-FOR'
