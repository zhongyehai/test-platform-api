# -*- coding: utf-8 -*-

import os

from config.config import basedir


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

if __name__ == '__main__':
    pass
