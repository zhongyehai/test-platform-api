# -*- coding: utf-8 -*-
import copy
import json

from flask import request


def save_log(app, result):
    """ 判断是否打日志 """
    if request.method == 'HEAD':
        return
    elif request.method == 'GET' and 'report' in request.path:  # 报告列表和报告详情都不打日志
        return
    elif 'run' in request.path:
        return
    else:
        app.logger.info(f'【{request.method}】【{request.url}】, \n响应数据:{json.loads(result[0])}')


def register_after_hook(app):
    """ 后置钩子函数，有请求时，会按函数所在位置，以从远到近的序顺序执行以下钩子函数，且每个钩子函数都必须返回响应对象 """

    @app.after_request
    def after_request(response_obj):
        """ 后置钩子函数，每个请求最后都会经过此函数 """
        if 'download' in request.path:
            return response_obj
        result = copy.copy(response_obj.response)
        if isinstance(result[0], bytes):
            result[0] = bytes.decode(result[0])
        save_log(app, result)
        return response_obj
