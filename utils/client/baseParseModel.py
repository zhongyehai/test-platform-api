# -*- coding: utf-8 -*-
import os

from utils.filePath import UI_CASE_FILE_ADDRESS
from utils.jsonUtil import JsonUtil
from config.config import assert_mapping
from utils.parse import extract_functions, parse_function, extract_variables


class BaseParseModel(JsonUtil):

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
        return {
            v['key']: self.build_data(v.get("data_type", "str"), v['value'])
            for v in variables_list if v.get('key') and v.get('value') is not None
        }

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
            [
                {"key": "project_id", "value": "content.data.id", "remark": "服务id", "update_to_header": True},
                {"key": "project_id1", "value": "content.data.id", "remark": "服务id", "update_to_header": False}
            ]
        return:
            {
                "extractors": [
                    {"project_id": "content.data.id"},
                    {"project_id1": "content.data.id"},
                ],
                "update_to_header_filed_list": ["project_id"]
            }
        """
        parsed = {
            "extractors": [],
            "update_to_header_filed_list": []
        }
        for extract in extracts_list:
            if extract.get('key') and extract.get('value'):
                parsed["extractors"].append({
                    extract['key']: self.build_extract_expression(extract.get('data_source'), extract['value'])
                })
                if extract.get("update_to_header"):
                    parsed["update_to_header_filed_list"].append(extract['key'])
        return parsed

    def parse_validates(self, validates_list):
        """ 解析断言
        validates:
            [
                {
                    "data_source": "content",
                    "data_type": "int",
                    "key": "status",
                    "remark": null,
                    "validate_type": "相等",
                    "value": "200"
                }
            ]
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
                    assert_mapping[validate_type]: [
                        self.build_actual_result(data_source, key),  # 实际结果
                        self.build_data(data_type, value)  # 预期结果
                    ]
                })
        return parsed_validate

    def build_data(self, data_type, value):
        """ 根据数据类型解析数据 """
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
        elif data_source == 'other':  # 其他数据，常量、自定义函数、自定义变量
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

    def parse_skip_if(self, skip_if_list):
        """ 判断 skip_if 是否要执行 """
        data_list = []
        for skip_if in skip_if_list:
            if skip_if and skip_if.get("expect"):
                skip_if["expect"] = self.build_data(skip_if["data_type"], skip_if["expect"])
                skip_if["comparator"] = assert_mapping[skip_if["comparator"]]
                data_list.append(skip_if)
        return data_list

    def parse_form_data(self, form_data_list):
        """ 解析form参数 """
        string, files = {}, {}
        for data in form_data_list:
            if data.get('key'):

                # 字符串
                if data['data_type'] == 'string':
                    string.update({data['key']: data['value']})

                # 上传文件，防止内存中有大对象，先把名字存下来，真正发请求的时候再读取文件
                elif data['data_type'] == 'file':
                    files.update({data['key']: data['value']})

        return string, files
