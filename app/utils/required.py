# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : required.py
# @Software: PyCharm
from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app, request
from flask_login import current_user

from app.utils import restful
from config.config import conf


def generate_reset_token(user, expiration=conf['token_time_out']):
    """ 生成token，默认有效期一个小时 """
    return Serializer(current_app.config['SECRET_KEY'], expiration).dumps(
        {'id': user.id, 'name': user.name}).decode('utf-8')


def parse_token(token):
    """ 校验token是否过期，或者是否合法 """
    try:
        data = Serializer(current_app.config['SECRET_KEY']).loads(token.encode('utf-8'))
        return data
    except:
        return False


def login_required(func):
    """ 校验用户的登录状态 token"""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # 前端拦截器检测到响应为 '登录超时,请重新登录' ，自动跳转到登录页
        return func(*args, **kwargs) if parse_token(request.headers.get('X-Token')) else restful.fail('登录超时,请重新登录')

    return decorated_view


def permission_required(permission_name):
    """ 校验当前用户是否有访问当前接口的权限 """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            return restful.forbidden('没有该权限') if not current_user.can(permission_name) else func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(func):
    """ 校验是否为管理员权限 """
    return permission_required('ADMINISTER')(func)
