# # -*- coding: utf-8 -*-
import os
import datetime
import threading

from loguru import logger

from utils.util.file_util import LOG_ADDRESS

log_format = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level} | "
    "PID: {extra[pid]} | "
    "Thread: {extra[tid]} | "
    "[{name}]:[{function}]:[{line}] | "
    "{message}"
)

logger.add(
    f'{LOG_ADDRESS}/{datetime.datetime.today().strftime("%Y-%m-%d")}.log',
    format=log_format,
    level="DEBUG",
    rotation="1 day",  # 每天切割
    retention="30 days",  # 保留30天
    diagnose=True,
    enqueue=True
)


# 使用一个自定义的函数来添加额外信息（进程ID和线程ID）
def add_extra_info(record):
    record["extra"]["pid"] = os.getpid()
    record["extra"]["tid"] = threading.get_ident()


# 配置 logger 以使用自定义函数
logger.configure(patcher=add_extra_info)
