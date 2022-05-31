#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : parse.py
# @Software: PyCharm
import ast
import importlib
import json
import re
import types
from app.utils.regexp import variable_regexp, function_regexp, function_regexp_compile


# variable_regexp = r"\$([\w_]+)"
# function_regexp = r"\$\{([\w_]+\([\$\w\.\-_ =,]*\))\}"
# function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")
# function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\W\.\-/_ =,]*)\)$")

def parse_list_to_dict(data_list: list):
    result = {}
    for data in data_list:
        if data['key']:
            result[data['key']] = {
                'key': data['key'],
                'value': data['value'],
                'remark': data['remark']
            }
    return result


def parse_dict_to_list(data_dict: dict):
    """
    {
        'a': {
            'key': 'a',
            'value': 123,
            'remark': '测试'
        }
    }
    """
    result = []
    for key, value in data_dict.items():
        result.append({
            'key': value['key'],
            'value': value['value'],
            'remark': value['remark'],
        })
    result.append({
        'key': None,
        'value': None,
        'remark': None,
    })
    return result


def extract_functions(content):
    """ 从字符串内容中提取所有自定义函数，格式为${fun()}
    @param (str) content
    @return (list) functions list

    e.g. ${func(5)} => ["func(5)"]
         ${func(a=1, b=2)} => ["func(a=1, b=2)"]
         /api_1_0/1000?_t=${get_timestamp()} => ["get_timestamp()"]
         /api_1_0/${add(1, 2)} => ["add(1, 2)"]
         "/api_1_0/${add(1, 2)}?_t=${get_timestamp()}" => ["add(1, 2)", "get_timestamp()"]
    """
    try:
        return re.findall(function_regexp, content)
    except TypeError:
        return []


def parse_function(content):
    """ 从字符串内容中解析函数名和参数
        >>> parse_function("func()")
        {'func_name': 'func', 'args': [], 'kwargs': {}}

        >>> parse_function("func(5)")
        {'func_name': 'func', 'args': [5], 'kwargs': {}}

        >>> parse_function("func(1, 2)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {}}

        >>> parse_function("func(a=1, b=2)")
        {'func_name': 'func', 'args': [], 'kwargs': {'a': 1, 'b': 2}}

        >>> parse_function("func(1, 2, a=3, b=4)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {'a':3, 'b':4}}

    """
    matched = function_regexp_compile.match(content)
    function_meta = {"func_name": matched.group(1), "args": [], "kwargs": {}}
    args_str = matched.group(2).strip()
    if args_str == "":
        return function_meta

    args_list = args_str.split(',')
    for arg in args_list:
        arg = arg.strip()
        if '=' in arg:
            key, value = arg.split('=')
            function_meta["kwargs"][key.strip()] = parse_string_value(value.strip())
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta


def extract_variables(content):
    """ 从内容中提取所有变量名，格式为$variable
    @param (str) content
    @return (list) variable name list

    e.g. $variable => ["variable"]
         /blog/$postid => ["postid"]
         /$var1/$var2 => ["var1", "var2"]
         abc => []
    """
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


def check_case(case_data, func_address):
    module_functions_dict = {}
    if func_address:
        for f in json.loads(func_address):
            import_path = 'func_list.{}'.format(f.replace('.py', ''))
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict.update({name: item for name, item in vars(func_list).items() if
                                          isinstance(item, types.FunctionType)})
            # module_functions_dict = dict(filter(is_function, vars(func_list).items()))

    if isinstance(case_data, list):
        for c in case_data:
            json_c = json.dumps(c)
            num = json_c.count('$')
            variable_num = len(extract_variables(json_c))
            func_num = len(extract_functions(json_c))
            if not c['case_name']:
                return '存在没有命名的用例，请检查'
            if num != (variable_num + func_num):
                return '‘{}’用例存在格式错误的引用参数或函数'.format(c['case_name'])
            if func_address:
                for func in extract_functions(json_c):
                    func = func.split('(')[0]
                    if func not in module_functions_dict:
                        return '{}用例中的函数“{}”在文件引用中没有定义'.format(c['case_name'], func)

    else:
        num = case_data.count('$')
        variable_num = len(extract_variables(case_data))
        func_num = len(extract_functions(case_data))
        if num != (variable_num + func_num):
            return '‘业务变量’存在格式错误的引用参数或函数'
        if func_address:
            for func in extract_functions(case_data):
                func = func.split('(')[0]
                if func not in module_functions_dict:
                    return '函数“{}”在文件引用中没有定义'.format(func)


def convert(variable):
    """ 同层次参数中，存在引用关系就先赋值
    eg:
        phone:123
        name:$phone
            ↓↓↓↓
        phone:123
        name:123
    """
    _temp = json.dumps(variable)
    content = {v['key']: v['value'] for v in variable if v['key'] != ''}
    for variable_name in extract_variables(_temp):
        if content.get(variable_name):
            # content contains one or several variables
            _temp = _temp.replace("${}".format(variable_name), str(content.get(variable_name)), 1)
            content = {v['key']: v['value'] for v in json.loads(_temp) if v['key'] != ''}

    return _temp


def parse_string_value(str_value):
    """ 字符串内容若能转为数字则转为数字
    e.g. "123" => 123
         "12.2" => 12.3
         "abc" => "abc"
         "$var" => "$var"
    """
    try:
        return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


def encode_object(obj):
    """ json.dumps转化时，先把属于bytes类型的解码，若解码失败返回str类型，和其他对象属性统一转化成str"""
    if isinstance(obj, bytes):
        try:
            return bytes.decode(obj)
        except Exception as e:
            return str(obj)
    else:
        return str(obj)

    # raise TypeError("{} is not JSON serializable".format(obj))


if __name__ == '__main__':
    # func_list = importlib.reload(importlib.import_module(r"func_list.abuild_in_fun.py"))
    # module_functions_dict = {name: item for name, item in vars(func_list).items() if
    #                          isinstance(item, types.FunctionType)}
    # print(module_functions_dict)
    a = '${func({"birthday": "199-02-02"; "expire_age": "65周岁"; "sex": "2"},123,3245)}'
    b = '${func([123],123)}'
    print(extract_functions(a))
    # matched = parse_function(extract_functions(b)[0])
    #
    # print(matched)
