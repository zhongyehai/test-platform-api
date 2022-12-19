# -*- coding: utf-8 -*-
from . import validator


def load_module_functions(module):
    """ 加载python模块中的函数
    Args:
        module: python模块
    Returns:
        模块中的函数: {"func1_name": func1, "func2_name": func2}
    """
    module_functions = {}
    for name, item in vars(module).items():
        if validator.is_function(item):
            module_functions[name] = item
    return module_functions


def load_builtin_functions():
    """ 加载 built_in 模块的函数 """
    from . import built_in
    return load_module_functions(built_in)
