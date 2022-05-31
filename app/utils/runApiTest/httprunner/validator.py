# encoding: utf-8
import os
import types

""" validate data format
TODO: refactor with JSON schema validate
"""


def is_testcase(data_structure):
    """ check if data_structure is a testcase.

    Args:
        data_structure (dict): testcase should always be in the following data structure:

            {
                "config": {
                    "name": "desc1",
                    "variables": [],    # optional
                    "request": {}       # optional
                },
                "teststeps": [
                    test_dict1,
                    {   # test_dict2
                        'name': 'test step desc2',
                        'variables': [],    # optional
                        'extract': [],      # optional
                        'validate': [],
                        'request': {},
                        'function_meta': {}
                    }
                ]
            }

    Returns:
        bool: True if data_structure is valid testcase, otherwise False.

    """
    # TODO: replace with JSON schema validation
    if not isinstance(data_structure, dict):
        return False

    if "teststeps" not in data_structure:
        return False

    if not isinstance(data_structure["teststeps"], list):
        return False

    return True


def is_testcases(data_structure):
    """ 判断 data_structure 是 testcase 还是 testcases 列表
    Args:
        data_structure (dict): testcase(s)为以下固定结构:
            {
                "project_mapping": {
                    "PWD": "XXXXX",
                    "functions": {},
                    "env": {}
                },
                "testcases": [
                    {   # testcase data structure
                        "config": {
                            "name": "desc1",
                            "path": "testcase1_path",
                            "variables": [],                    # optional
                        },
                        "teststeps": [
                            # test data structure
                            {
                                'name': 'test step desc1',
                                'variables': [],    # optional
                                'extract': [],      # optional
                                'validate': [],
                                'request': {}
                            },
                            test_dict_2   # another test dict
                        ]
                    },
                    testcase_dict_2     # another testcase dict
                ]
            }

    Returns:
        如果是testcase 或者 testcases 列表，则返回True，否则返回False
    """
    if not isinstance(data_structure, dict):
        return False
    return True


def is_testcase_path(path):
    """ 判断path是否为 文件路径 或 路径列表，如果路径是有效的文件路径或路径列表，返回True，否则返回False """
    if not isinstance(path, (str, list)):
        return False

    if isinstance(path, list):
        for p in path:
            if not is_testcase_path(p):
                return False

    if isinstance(path, str):
        if not os.path.exists(path):
            return False

    return True


#  验证变量和函数

def is_function(item):
    """ 判断传进来的 item对象 是否为函数 """
    return isinstance(item, types.FunctionType)


def is_variable(tup):
    """ 接受（name，object）元组，如果它是变量，则返回True """
    name, item = tup
    # if callable(item):  # 类或者方法
    #     return False
    #
    # if isinstance(item, types.ModuleType):  # 模块
    #     return False
    #
    # if name.startswith("_"):  # 私有属性
    #     return False

    if callable(item) or isinstance(item, types.ModuleType) or name.startswith("_"):  # 类或者方法、模块、私有属性
        return False

    return True
