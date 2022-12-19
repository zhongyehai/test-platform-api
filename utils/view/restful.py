# -*- coding: utf-8 -*-
import json


def restful_result(code, message, data, **kwargs):
    """ 统一返 result风格 """
    return json.dumps({"status": code, "message": message, "data": data, **kwargs}, ensure_ascii=False)


def success(msg=None, data=None, **kwargs):
    """ 业务处理成功的响应 """
    return restful_result(code=200, message=msg or "处理成功", data=data, **kwargs)


def get_success(data=None, **kwargs):
    """ 数据获取成功的响应 """
    return success(msg="获取成功", data=data, **kwargs)


def fail(msg=None, data=None, **kwargs):
    """ 业务处理失败的响应 """
    return restful_result(code=400, message=msg or "处理失败", data=data, **kwargs)


def not_login(msg=None, data=None, **kwargs):
    """ 未登录的响应 """
    return restful_result(code=401, message=msg or "请重新登录", data=data, **kwargs)


def forbidden(msg=None, data=None, **kwargs):
    """ 权限不足的响应 """
    return restful_result(code=403, message=msg or "权限不足", data=data, **kwargs)


def url_not_find(msg=None, data=None, **kwargs):
    """ url不存在的响应 """
    return restful_result(code=404, message=msg or "url不存在", data=data, **kwargs)


def error(msg=None, data=None, **kwargs):
    """ 系统发送错误的响应 """
    return restful_result(code=500, message=msg or "系统出错了，请联系开发人员查看", data=data, **kwargs)
