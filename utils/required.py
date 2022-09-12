# -*- coding: utf-8 -*-

from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app as app, request, g


# from utils import restful


def parse_token(token):
    """ 校验token是否过期，或者是否合法 """
    try:
        from app.system.models.user import User
        data = Serializer(app.config['SECRET_KEY']).loads(token.encode('utf-8'))
        g.user_id, g.user_name, g.user_role = data['id'], data['name'], data['role']  # 把用户数据存到g对象，方便后面使用
        return True
    except:
        return False


def login_required(func):
    """ 校验用户的登录状态 token"""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # 前端拦截器检测到响应为 '登录超时,请重新登录' ，自动跳转到登录页
        if not g.get("user_id"):
            return app.restful.not_login()
        return func(*args, **kwargs)

    return decorated_view


def admin_required(func):
    """ 校验当前用户是否有访问当前接口的权限 """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if g.get("user_role") != 2:
            return app.restful.forbidden(msg='没有权限')
        return func(*args, **kwargs)

    return decorated_function


def before_request_required():
    """ 校验用户的登录状态或者权限"""
    parse_token(request.headers.get('X-Token'))
    # if request.endpoint.endswith('is_admin_required'):  # 终结点以 is_admin_required 结尾，则校验登录状态和用户权限
    #     base_login_required()
    #     base_admin_required()
    # elif not request.endpoint.endswith('not_login_required'):  # 终结点不以 not_login_required 结尾，则校验登录状态
    #     base_login_required()

# def login_required():
#     """ 校验用户的登录状态 token"""
#     if not g.user_id:
#         abort(401)


# def base_admin_required():
#     """ 校验用户是否为管理员 """
#     if g.user_role != 2:
#         abort(403)
