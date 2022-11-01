# -*- coding: utf-8 -*-
import json
import os
import io

from config import basedir
from utils.variables.contentType import CONTENT_TYPE

# 各模块的路径
LOG_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/logs/'))  # 日志路径
RUN_LOG_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/run_logs/'))  # 日志路径
STATIC_ADDRESS = os.path.abspath(os.path.join(basedir, r'static'))  # 导入模板存放路径
FUNC_ADDRESS = os.path.abspath(os.path.join(basedir, '.' + r'/func_list'))  # 自定义函数文件存放地址
API_REPORT_ADDRESS = os.path.abspath(os.path.join(basedir, ".." + r'/reports_api/'))  # api测试报告文件存放地址
WEB_UI_REPORT_ADDRESS = os.path.abspath(os.path.join(basedir, ".." + r'/reports_web_ui/'))  # web-ui测试报告文件存放地址
APP_UI_REPORT_ADDRESS = os.path.abspath(os.path.join(basedir, ".." + r'/reports_app_ui/'))  # app-ui测试报告文件存放地址
DIFF_RESULT = os.path.abspath(os.path.join(basedir, ".." + r'/diff_result/'))  # yapi接口监控结果存放地址
CASE_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/case_files/'))  # 用例数据文件存放地址
UI_CASE_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/ui_case_files/'))  # ui用例数据文件存放地址
MOCK_DATA_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/mock_data/'))  # mock数据文件存放地址
CALL_BACK_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/call_back/'))  # 回调数据文件存放地址
CFCA_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/cfca_files/'))  # CFCA文件存放地址
TEMP_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/temp_files/'))  # 临时文件存放地址
GIT_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/git_files/'))  # git文件存放地址
SWAGGER_FILE_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/swagger_files/'))  # swagger文件存放地址
DB_BACK_UP_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/db_back_up_files/'))  # 数据库备份地址
BROWSER_DRIVER_ADDRESS = os.path.abspath(os.path.join(basedir, '..' + r'/browser_drivers/'))  # 浏览器驱动文件存放地址


def _check_file_path(paths):
    """ 校验各模块的路径是否存在，若不存在则创建 """
    if isinstance(paths, (list, tuple, set)):
        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)
    else:
        if not os.path.exists(paths):
            os.makedirs(paths)


_check_file_path([
    LOG_ADDRESS, FUNC_ADDRESS, API_REPORT_ADDRESS, WEB_UI_REPORT_ADDRESS, APP_UI_REPORT_ADDRESS, DIFF_RESULT,
    CASE_FILE_ADDRESS, UI_CASE_FILE_ADDRESS, MOCK_DATA_ADDRESS, CALL_BACK_ADDRESS, CFCA_FILE_ADDRESS, TEMP_FILE_ADDRESS,
    GIT_FILE_ADDRESS, DB_BACK_UP_ADDRESS, SWAGGER_FILE_ADDRESS, RUN_LOG_ADDRESS, BROWSER_DRIVER_ADDRESS
])

run_api_test_log = os.path.join(RUN_LOG_ADDRESS, 'api_test.log')
run_ui_test_log = os.path.join(RUN_LOG_ADDRESS, 'ui_test.log')


class FileUtil:

    @classmethod
    def build_request_file(cls, file_dict):
        """ 构建接口自动化文件请求对象 """
        request_file = {}
        for key, value in file_dict.items():
            request_file[key] = (
                value,  # 文件名
                open(os.path.join(CASE_FILE_ADDRESS, value), 'rb'),  # 文件流
                CONTENT_TYPE.get(f'.{value.split(".")[-1]}', "text/html")  # content-type，根据文件后缀取，如果没有预设此项，则默认取text
            )
        return request_file

    @classmethod
    def save_file(cls, path, content):
        """ 保存文件 """
        with io.open(path, 'w', encoding='utf-8') as file:
            if isinstance(content, str):
                file.write(content)
            else:
                json.dump(content, file, ensure_ascii=False, indent=4)

    @classmethod
    def delete_file(cls, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

    @classmethod
    def save_api_test_report(cls, report_id, content):
        """ 保存接口自动化测试报告 """
        cls.save_file(os.path.join(API_REPORT_ADDRESS, f'{report_id}.txt'), content)

    @classmethod
    def save_web_ui_test_report(cls, report_id, content):
        """ 保存web_ui自动化测试报告 """
        cls.save_file(os.path.join(WEB_UI_REPORT_ADDRESS, f'{report_id}.txt'), content)

    @classmethod
    def save_app_ui_test_report(cls, report_id, content):
        """ 保存app_ui自动化测试报告 """
        cls.save_file(os.path.join(APP_UI_REPORT_ADDRESS, f'{report_id}.txt'), content)

    @classmethod
    def save_diff_result(cls, diff_record_id, diff_detail):
        """ 保存对比数据 """
        with io.open(os.path.join(DIFF_RESULT, f'{diff_record_id}.json'), 'w', encoding='utf-8') as fp:
            json.dump(diff_detail, fp, ensure_ascii=False, indent=4)

    @classmethod
    def save_func_data(cls, name, content, env='test'):
        """ 保存自定义函数数据 """
        func_data = '# coding:utf-8\n\n' + f'env = "{env}"\n\n' + content
        cls.save_file(os.path.join(FUNC_ADDRESS, f'{name}.py'), func_data)

    @classmethod
    def get_report(cls, file_path, report_id):
        """ 获取自动化测试报告 """
        with io.open(os.path.join(file_path, f'{report_id}.txt'), 'r', encoding='utf-8') as file:
            report_content = json.load(file)
        return report_content

    @classmethod
    def get_api_test_report(cls, report_id):
        """ 获取接口自动化测试报告 """
        return cls.get_report(API_REPORT_ADDRESS, report_id)

    @classmethod
    def get_web_ui_test_report(cls, report_id):
        """ 获取web_ui自动化测试报告 """
        return cls.get_report(WEB_UI_REPORT_ADDRESS, report_id)

    @classmethod
    def get_app_ui_test_report(cls, report_id):
        """ 获取app_ui自动化测试报告 """
        return cls.get_report(APP_UI_REPORT_ADDRESS, report_id)

    @classmethod
    def get_diff_result(cls, diff_id):
        """ 获取对比数据 """
        with io.open(os.path.join(DIFF_RESULT, f'{diff_id}.json'), 'r', encoding='utf-8') as fp:
            diff_data = json.load(fp)
        return diff_data

    @classmethod
    def build_ui_test_file_path(cls, filename):
        """ 拼装UI自动化要上传文件的路径 """
        return os.path.join(UI_CASE_FILE_ADDRESS, filename)


if __name__ == '__main__':
    pass
