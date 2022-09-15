# -*- coding: utf-8 -*-
from utils.client.baseParseModel import BaseParseModel as _BaseParseModel


class BaseParseModel(_BaseParseModel):

    def parse_body(self, kwargs):
        """ 根据请求体数据类型解析请求体 """
        if self.data_type in ['json', 'raw']:
            self.data_json = kwargs.get('data_json', {})
        elif self.data_type in ['form', 'data']:
            self.data_form, self.data_file = self.parse_form_data(kwargs.get('data_form', {}))
        elif self.data_type == 'urlencoded':
            self.data_form = kwargs.get('data_urlencoded', {})
            self.headers["Content-Type"] = 'application/x-www-form-urlencoded'
        elif self.data_type in ['xml', 'text']:
            self.data_form = kwargs.get('data_text', '')


class ProjectFormatModel(BaseParseModel):
    """ 格式化服务信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.manager = kwargs.get('manager')
        self.func_files = kwargs.get('func_files')
        self.create_user = kwargs.get('create_user')
        self.test = kwargs.get('test')
        self.host = kwargs.get('host')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))


class ApiFormatModel(BaseParseModel):
    """ 格式化接口信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.time_out = kwargs.get('time_out')
        self.desc = kwargs.get('desc')
        self.up_func = kwargs.get('up_func')
        self.down_func = kwargs.get('down_func')
        self.env = kwargs.get('env')
        self.method = kwargs.get('method')
        self.addr = kwargs.get('addr')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.params = self.parse_params(kwargs.get('params', {}))
        self.extracts = self.parse_extracts(kwargs.get('extracts', []))
        self.validates = self.parse_validates(kwargs.get('validates', {}))
        self.module_id = kwargs.get('module_id')
        self.project_id = kwargs.get('project_id')
        self.create_user = kwargs.get('create_user')

        # 根据数据类型解析请求体
        self.data_type = kwargs.get('data_type', 'json')
        self.data_json, self.data_form, self.data_file = {}, {}, {}
        self.parse_body(kwargs)


class CaseFormatModel(BaseParseModel):
    """ 格式化用例信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.env = kwargs.get('env')
        self.func_files = kwargs.get('func_files')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))
        self.is_run = kwargs.get('is_run')
        self.run_times = kwargs.get('run_times')
        self.module_id = kwargs.get('module_id')
        self.create_user = kwargs.get('create_user')


class StepFormatModel(BaseParseModel):
    """ 格式化步骤信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.time_out = kwargs.get('time_out')
        self.run_times = kwargs.get('run_times')
        self.up_func = kwargs.get('up_func')
        self.down_func = kwargs.get('down_func')
        self.skip_if = self.parse_skip_if(kwargs.get('skip_if'))
        self.is_run = kwargs.get('is_run')
        self.replace_host = kwargs.get('replace_host')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.params = self.parse_params(kwargs.get('params', {}))
        self.extracts = self.parse_extracts(kwargs.get('extracts', []))
        self.validates = self.parse_validates(kwargs.get('validates', {}))
        self.data_driver = kwargs.get('data_driver', {})
        self.quote_case = kwargs.get('quote_case', {})
        self.case_id = kwargs.get('case_id')
        self.api_id = kwargs.get('api_id')
        self.project_id = kwargs.get('project_id')
        self.create_user = kwargs.get('create_user')

        # 根据数据类型解析请求体
        self.data_type = kwargs.get('data_type', 'json')
        self.data_json, self.data_form, self.data_file = {}, {}, {}
        self.parse_body(kwargs)
