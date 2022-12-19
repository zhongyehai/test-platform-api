# -*- coding: utf-8 -*-
import os
import email
import six

import urllib3.fields as f
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from utils.client.testRunner import built_in as assert_func_file
from utils.client.testRunner.webdriverAction import Actions

# 从 testRunner.built_in 中获取断言方式并映射为字典和列表，分别给前端和运行测试用例时反射断言
assert_mapping, assert_mapping_list = {}, []
for func in dir(assert_func_file):
    if func.startswith("_") and not func.startswith("__"):
        doc = getattr(assert_func_file, func).__doc__.strip()  # 函数注释
        assert_mapping.setdefault(doc, func)
        assert_mapping_list.append({"value": doc})

# UI自动化的行为事件
action_mapping = Actions.get_action_mapping()
ui_action_mapping, ui_action_mapping_list = action_mapping["mapping_dict"], action_mapping["mapping_list"]
ui_action_mapping_reverse = dict(zip(ui_action_mapping.values(), ui_action_mapping.keys()))

# UI自动化的断言事件
ui_assert_mapping = Actions.get_assert_mapping()
ui_assert_mapping, ui_assert_mapping_list = ui_assert_mapping["mapping_dict"], ui_assert_mapping["mapping_list"]

# UI自动化的数据提取事件
extract_mapping = Actions.get_extract_mapping()
ui_extract_mapping, ui_extract_mapping_list = extract_mapping["mapping_dict"], extract_mapping["mapping_list"]
ui_extract_mapping.setdefault("自定义函数", "func")
ui_extract_mapping_list.append({"label": "自定义函数", "value": "func"})

# 跳过条件判断类型映射
skip_if_type_mapping = [
    {"label": "满足则跳过", "value": "skip_if_true"},
    {"label": "不满足则跳过", "value": "skip_if_false"},
]

# 跳过条件数据源映射
skip_if_data_source_mapping = [
    {"label": "运行环境", "value": "run_env"}
]

basedir = os.path.abspath(".")

# 即时达推送的 系统错误通道，不接受错误信息可不配置
error_push = {
    "url": "http://push.ijingniu.cn/send",
    "key": ""
}


def my_format_header_param(name, value):
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    if not six.PY3 and isinstance(value, six.text_type):  # Python 2:
        value = value.encode("utf-8")
    value = email.utils.encode_rfc2231(value, "utf-8")
    value = "%s*=%s" % (name, value)
    return value


# 猴子补丁，修复request上传文件时，不能传中文
f.format_header_param = my_format_header_param


class ProductionConfig:
    """ 生产环境配置 """

    SECRET_KEY = ""  # 随便填个字符串
    TOKEN_TIME_OUT = 36000
    CSRF_ENABLED = True

    # 数据库信息
    DB_HOST = ""
    DB_PORT = ""
    DB_USER = ""
    DB_PASSWORD = ""
    DB_DATABASE = ""

    ERROR_PUSH_URL = error_push.get("url")
    ERROR_PUSH_KEY = error_push.get("key")

    # 数据库链接
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}?charset=utf8mb4&autocommit=true"

    # 关闭数据追踪，避免内存资源浪费
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 关闭自动提交，若开启自动提交会出现以下报错
    # sqlalchemy.exc.InvalidRequestError: Can"t reconnect until invalid transaction is rolled back
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False

    # 每次连接从池中检查，如果有错误，监测为断开的状态，连接将被立即回收。
    SQLALCHEMY_POOL_PRE_PING = True

    # 数据库连接池的大小。默认是数据库引擎的默认值默认是5
    SQLALCHEMY_POOL_SIZE = 200

    # 当连接池达到最大值后可以创建的连接数。当这些额外的连接处理完回收后，若没有在等待进程获取连接，这个连接将会被立即释放。
    SQLALCHEMY_MAX_OVERFLOW = 1000

    # 从连接池里获取连接
    # 如果此时无空闲的连接，且连接数已经到达了pool_size+max_overflow。此时获取连接的进程会等待pool_timeout秒。
    # 如果超过这个时间，还没有获得将会抛出异常。
    # 默认是30秒
    SQLALCHEMY_POOL_TIMEOUT = 30

    # 一个数据库连接的生存时间。
    #     例如pool_recycle=3600。也就是当这个连接产生1小时后，再获得这个连接时，会丢弃这个连接，重新创建一个新的连接。
    #
    # 当pool_recycle设置为-1时，也就是连接池不会主动丢弃这个连接。永久可用。但是有可能数据库server设置了连接超时时间。
    #     例如mysql，设置的有wait_timeout默认为28800，8小时。当连接空闲8小时时会自动断开。8小时后再用这个连接也会被重置。
    SQLALCHEMY_POOL_RECYCLE = 3600  # 1个小时

    # 输出SQL语句
    # SQLALCHEMY_ECHO = True

    # flask_apscheduler 定时任务存储配置
    SCHEDULER_JOBSTORES = {
        "default": SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }
    # flask_apscheduler 线程池配置
    SCHEDULER_EXECUTORS = {
        "default": {"type": "threadpool", "max_workers": 20}
    }
    SCHEDULER_JOB_DEFAULTS = {
        "coalesce": False,
        "max_instances": 2,
        "misfire_grace_time": None
    }
    SCHEDULER_TIMEZONE = "Asia/Shanghai"  # 时区
    SCHEDULER_API_ENABLED = True  # 开启API访问功能
    SCHEDULER_API_PREFIX = "/api/scheduler"  # api前缀（默认是/scheduler）


if __name__ == "__main__":
    pass
