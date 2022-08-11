# -*- coding: utf-8 -*-

import os

from utils.globalVariable import UI_CASE_FILE_ADDRESS
from utils.jsonUtil import JsonUtil


class Base(JsonUtil):

    def build_file_path(self, filename):
        """ 拼装要上传文件的路径 """
        return os.path.join(UI_CASE_FILE_ADDRESS, filename)

    def parse_headers(self, headers_list):
        """ 解析头部信息
        headers_list:
            [{"key": "x-auth-token", "value": "aaa"}, {"key": null, "value": null}]
        :return
            {"x-auth-token": "aaa"}
        """
        return {header['key']: header['value'] for header in headers_list if header.get('key')}

    def parse_variables(self, variables_list):
        """ 解析公用变量
        variables_list:
            [
                {"key":"auto_test_token","remark":"token","value":"eyJhbGciOiJIUzI1NiJ9"},
                {"key":"rating_amount","remark":"申请金额","value":"500000"}
            ]
        :return
            {"auto_test_token": "eyJhbGciOiJIUzI1NiJ9", "rating_amount": "500000"}
        """
        return {v['key']: v['value'] for v in variables_list if v.get('key') and v.get('value') is not None}


class ProjectFormatModel(Base):
    """ 格式化服务信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.manager = kwargs.get('manager')
        self.func_files = kwargs.get('func_files')
        self.create_user = kwargs.get('create_user')
        self.test = kwargs.get('test')
        self.host = kwargs.get('host')
        self.variables = self.parse_variables(kwargs.get('variables', [{}]))
        self.cookies = self.parse_headers(kwargs.get('cookies', [{}]))
        self.session_storage = self.parse_headers(kwargs.get('session_storage', [{}]))
        self.local_storage = self.parse_headers(kwargs.get('local_storage', [{}]))


class ElementFormatModel(Base):
    """ 格式化元素信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.by = kwargs.get('by')
        self.element = kwargs.get('element')
        self.wait_time_out = kwargs.get('wait_time_out')
        self.page_id = kwargs.get('page_id')
        self.module_id = kwargs.get('module_id')
        self.project_id = kwargs.get('project_id')


class CaseFormatModel(Base):
    """ 格式化用例信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.env = kwargs.get('env')
        self.func_files = kwargs.get('func_files')
        self.variables = self.parse_variables(kwargs.get('variables', [{}]))
        self.cookies = self.parse_headers(kwargs.get('cookies', [{}]))
        self.session_storage = self.parse_headers(kwargs.get('session_storage', [{}]))
        self.local_storage = self.parse_headers(kwargs.get('local_storage', [{}]))
        self.is_run = kwargs.get('is_run')
        self.run_times = kwargs.get('run_times')
        self.module_id = kwargs.get('module_id')
        self.create_user = kwargs.get('create_user')


class StepFormatModel(Base):
    """ 格式化步骤信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.wait_time_out = kwargs.get('wait_time_out')
        self.run_times = kwargs.get('run_times')
        self.up_func = kwargs.get('up_func')
        self.down_func = kwargs.get('down_func')
        self.is_run = kwargs.get('is_run')
        self.execute_type = kwargs.get('execute_type')
        self.send_keys = self.parse_send_keys(kwargs.get('send_keys'))
        self.extracts = kwargs.get('extracts', [])
        self.validates = kwargs.get('validates', {})
        self.data_driver = kwargs.get('data_driver', {})
        self.quote_case = kwargs.get('quote_case', {})
        self.project_id = kwargs.get('project_id')
        self.page_id = kwargs.get('page_id')
        self.element_id = kwargs.get('element_id')
        self.case_id = kwargs.get('case_id')
        self.create_user = kwargs.get('create_user')

    def parse_send_keys(self, send_keys):
        """ 解析输入内容 """
        return self.build_file_path(send_keys) if '_is_upload' in send_keys else send_keys
