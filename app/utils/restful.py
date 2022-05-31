#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : restful.py
# @Software: PyCharm
from flask import jsonify


class HttpCode:
    """ 定义一些约定好的业务处理状态 """

    success = {'code': 200, 'message': '处理成功'}
    fail = {'code': 400, 'message': '处理失败'}
    forbidden = {'code': 403, 'message': '权限不足'}
    not_find = {'code': 404, 'message': 'url不存在'}
    error = {'code': 500, 'message': '系统出错了，请联系开发人员查看'}


def restful_result(code, message, data, **kwargs):
    """ 统一返 result风格 """
    return jsonify({'status': code, 'message': message, 'data': data, **kwargs})


def success(msg=HttpCode.success['message'], data=None, **kwargs):
    """ 业务处理成功的响应 """
    return restful_result(code=HttpCode.success['code'], message=msg, data=data, **kwargs)


def get_success(data=None, **kwargs):
    """ 数据获取成功的响应 """
    return success(msg='获取成功', data=data, **kwargs)


def fail(msg=HttpCode.fail['message'], data=None, **kwargs):
    """ 业务处理失败的响应 """
    return restful_result(code=HttpCode.fail['code'], message=msg, data=data, **kwargs)


def forbidden(msg=HttpCode.forbidden['message'], data=None, **kwargs):
    """ 权限不足的响应 """
    return restful_result(code=HttpCode.forbidden['code'], message=msg, data=data, **kwargs)


def url_not_find(msg=HttpCode.not_find['message'], data=None, **kwargs):
    """ url不存在的响应 """
    return restful_result(code=HttpCode.not_find['code'], message=msg, data=data, **kwargs)


def error(msg=HttpCode.error['message'], data=None, **kwargs):
    """ 系统发送错误的响应 """
    return restful_result(code=HttpCode.error['code'], message=msg, data=data, **kwargs)
