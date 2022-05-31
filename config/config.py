# -*- coding: utf-8 -*-

import os
import email
import six

import urllib3.fields as f
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.utils.yamlUtil import load
from app.utils.runApiTest.httprunner import built_in as assert_func_file
from app.utils.runUiTest.uitestrunner.webdriverAction import Driver

# 从 httpRunner.built_in 中获取断言方式并映射为字典和列表，分别给前端和运行测试用例时反射断言
assert_mapping, assert_mapping_list = {}, []
for func in dir(assert_func_file):
    if func.startswith('_') and not func.startswith('__'):
        doc = getattr(assert_func_file, func).__doc__.strip()  # 函数注释
        assert_mapping.setdefault(doc, func)
        assert_mapping_list.append({'value': doc})

# UI自动化的行为事件
action_mapping = Driver.get_action_mapping()
ui_action_mapping, ui_action_mapping_list = action_mapping['mapping_dict'], action_mapping['mapping_list']
ui_action_mapping_reverse = dict(zip(ui_action_mapping.values(), ui_action_mapping.keys()))

# UI自动化的断言事件
ui_assert_mapping = Driver.get_assert_mapping()
ui_assert_mapping, ui_assert_mapping_list = ui_assert_mapping['mapping_dict'], ui_assert_mapping['mapping_list']

# UI自动化的数据提取事件
extract_mapping = Driver.get_extract_mapping()
ui_extract_mapping, ui_extract_mapping_list = extract_mapping['mapping_dict'], extract_mapping['mapping_list']
ui_extract_mapping.setdefault('自定义函数', 'func')
ui_extract_mapping_list.append({'label': '自定义函数', 'value': 'func'})

basedir, conf = os.path.abspath('.'), load(os.path.abspath('.') + '/config/config.yaml')


def my_format_header_param(name, value):
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    if not six.PY3 and isinstance(value, six.text_type):  # Python 2:
        value = value.encode('utf-8')
    value = email.utils.encode_rfc2231(value, 'utf-8')
    value = '%s*=%s' % (name, value)
    return value


# 猴子补丁，修复request上传文件时，不能传中文
f.format_header_param = my_format_header_param


class ProductionConfig:
    """ 生产环境数据库 """
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://' \
                              f'{conf["db"]["user"]}:' \
                              f'{conf["db"]["password"]}@' \
                              f'{conf["db"]["host"]}:' \
                              f'{conf["db"]["port"]}/' \
                              f'{conf["db"]["database"]}?charset=utf8mb4'
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(
            url=SQLALCHEMY_DATABASE_URI,
            # engine_options={
            #     'pool_pre_ping': True,  # 连接时ping一下数据库，连不上则回收一次
            #     'pool_size': 10,
            #     'pool_recycle': 120,  # 120秒回收一次数据库连接
            # }
        )
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_PRE_PING = True  # 每次请求前先预先请求一次数据库，一旦预先请求出错则重新建立数据库连接
    SQLALCHEMY_POOL_SIZE = 1000  # 连接池大小
    SQLALCHEMY_POOL_RECYCLE = 10  # 空闲时间超过10秒则重新连接数据库，这个值实测设大了会失效（即使小于mysql的time—waite也会报错）

    SECRET_KEY = conf['SECRET_KEY']
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    CSRF_ENABLED = True
    UPLOAD_FOLDER = '/upload'
    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        pass


if __name__ == '__main__':
    pass
