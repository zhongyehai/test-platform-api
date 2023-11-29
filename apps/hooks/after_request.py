# -*- coding: utf-8 -*-
import copy
import json

from flask import request, g

from utils.logs.log import logger


def save_response_log(result):
    """ 判断是否打日志
    HEAD请求不打日志
    run请求不打日志
    获取报告详情不打日志
    """
    if request.method == "HEAD" or request.path.endswith("report/detail") or request.path.endswith("/report/step/img"):
        return
    else:
        logger.info(
            f'【{g.get("user_name")}】【{g.user_ip}】【{request.method}】【{request.url}】, \n响应数据:{json.loads(result[0])}\n')


def register_after_hook(app):
    """ 后置钩子函数，有请求时，会按函数所在位置，以从远到近的序顺序执行以下钩子函数，且每个钩子函数都必须返回响应对象 """

    @app.after_request
    def after_request_save_response_log(response_obj):
        """ 后置钩子函数，每个请求最后都会经过此函数 """
        if "download" in request.path or "." in request.path or request.path.endswith("swagger"):
            return response_obj
        result = copy.copy(response_obj.response)
        if isinstance(result[0], bytes):
            result[0] = bytes.decode(result[0])
        save_response_log(result)
        return response_obj
