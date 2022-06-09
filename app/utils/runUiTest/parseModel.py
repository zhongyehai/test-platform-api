# -*- coding: utf-8 -*-

import os

from ..globalVariable import UI_CASE_FILE_ADDRESS
from ..jsonUtil import JsonUtil
from ..parse import extract_functions, parse_function, extract_variables


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

    def parse_params(self, params_list):
        """ 解析查询字符串参数
        params_list:
            [{"key": "name", "value": "aaa"}]
        :return
            {"name": "aaa"}
        """
        return {p['key']: p['value'] for p in params_list if p.get('key') and p.get('value') is not None}

    def parse_extracts(self, extracts_list):
        """ 解析要提取的参数
        extracts_list:
            [{"key": "project_id", "value": "content.data.id", "remark": "服务id"}]
        return:
            [{"project_id": "content.data.id"}]
        """
        return [
            {
                extract['key']: self.build_extract_expression(extract.get('data_source'), extract['value'])
            } for extract in extracts_list if extract.get('key')
        ]

    def parse_validates(self, validates_list):
        """ 解析断言
        validates:
            [{"key": "1", "value": "content.message", "validate_type": "equals"}]
        return:
            [{"equals": ["1", "content.message"]}]
        """
        parsed_validate = []
        for validate in validates_list:
            data_source, key = validate.get('data_source'), validate.get('key')
            validate_type = validate.get('validate_type')
            data_type, value = validate.get('data_type'), validate.get('value')
            if data_source and data_type:
                parsed_validate.append({
                    validate_type: [
                        data_source,  # 实际结果
                        self.build_expect_result(data_type, value)  # 预期结果
                    ]
                })
        return parsed_validate

    def build_expect_result(self, data_type, value):
        """ 生成预期结果 """
        if data_type in ["variable", "func", 'str']:
            return value
        elif data_type == 'json':
            return self.dumps(self.loads(value))
        else:  # python数据类型
            return eval(f'{data_type}({value})')

    def build_actual_result(self, data_source, key):
        """ 生成实际结果表达式 """
        if data_source == 'regexp':  # 正则表达式
            return key
        elif not key:  # 整个指定的响应对象
            return data_source
        else:
            return f'{data_source}.{key}'

    def build_extract_expression(self, data_source, key):
        """ 生成数据提取表达式 """

        # 自定义函数
        ext_func = extract_functions(key)
        if ext_func:  # 自定义函数
            return self.build_func_expression(ext_func, data_source)
        elif data_source == 'regexp':  # 正则表达式
            return key
        elif not key:  # 整个指定的响应对象
            return data_source
        else:  # 自定义函数
            return f'{data_source}.{key}'

    def build_func_expression(self, ext_func, data_source):
        """ 解析自定义函数的提取表达式，并生成新的表达式 """
        func = parse_function(ext_func[0])
        func_name, args, kwargs = func['func_name'], func['args'], func['kwargs']

        args_and_kwargs = []
        # 处理args参数
        for arg in args:
            # 如果是自定义变量则不改变, 如果不是，则把数据源加上
            if extract_variables(arg).__len__() >= 1:
                args_and_kwargs.append(arg)
            else:
                args_and_kwargs.append(f'{data_source}.{arg}')

        # 处理kwargs参数
        for kw_key, kw_value in kwargs.items():
            # 如果是自定义变量则不改变, 如果不是，则把数据源加上
            if extract_variables(kw_value).__len__() >= 1:
                args_and_kwargs.append(f'{kw_key}={kw_value}')
            else:
                args_and_kwargs.append(f'{kw_key}={data_source}.{kw_value}')

        return '${' + f'{func_name}({",".join(args_and_kwargs)})' + '}'


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
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))


class ElementFormatModel(Base):
    """ 格式化元素信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.by = kwargs.get('by')
        self.element = kwargs.get('element')
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
        self.choice_host = kwargs.get('choice_host')
        self.func_files = kwargs.get('func_files')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))
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
