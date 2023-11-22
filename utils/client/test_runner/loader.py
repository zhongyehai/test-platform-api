# # -*- coding: utf-8 -*-
# import types
#
#  # TODO 放到 validate_func 脚本，参照函数文件，用this
# def load_module_functions(module):
#     """ 加载python模块中的函数
#     Args:
#         module: python模块
#     Returns:
#         模块中的函数: {"func1_name": func1, "func2_name": func2}
#     """
#     module_functions = {}
#     for name, item in vars(module).items():
#         if isinstance(item, types.FunctionType):
#             module_functions[name] = item
#     return module_functions
#
#
# def load_builtin_functions():
#     """ 加载 validate_func 模块的函数 """
#     from . import validate_func
#     return load_module_functions(validate_func)
