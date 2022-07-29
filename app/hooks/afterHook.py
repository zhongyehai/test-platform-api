# -*- coding: utf-8 -*-
import copy
import json

from flask import request


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
        # 减少日志数据打印，跑用例的数据均不打印到日志
        if 'apiMsg/run' not in request.path and 'report/run' not in request.path and 'report/list' not in request.path and request.method != 'HEAD':
            app.logger.info(f'{request.method}==>{request.url}, 返回数据:{json.loads(result[0])}')
        return response_obj
