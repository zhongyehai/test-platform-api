# -*- coding: utf-8 -*-
from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app as app, request, g


def parse_token(token):
    """ 校验token是否过期，或者是否合法 """
    try:
        from app.system.models.user import User
        data = Serializer(app.config["SECRET_KEY"]).loads(token.encode("utf-8"))
        # 把用户数据存到g对象，方便后面使用
        g.user_id, g.user_name = data["id"], data["name"]
        g.api_permissions, g.business_list = data["api_permissions"], data["business_list"]
        return True
    except:
        g.user_id, g.user_name, g.api_permissions, g.business_list = None, None, [], []
        return False


def login_required(func):
    """ 校验用户的登录状态 token"""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # 前端拦截器检测到响应为 "登录超时,请重新登录" ，自动跳转到登录页
        from app.system.models.user import User
        if not g.get("user_id"):  # 检验登录
            return app.restful.not_login()
        # elif User.is_not_admin() and request.path not in g.api_permissions:  # 校验接口权限
        #     return app.restful.forbidden(msg="没有权限")
        return func(*args, **kwargs)

    return decorated_view


def permission_required(func):
    """ 校验当前用户是否有访问当前接口的权限 """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        from app.system.models.user import User
        if User.is_admin() or request.path in g.api_permissions:  # 校验接口权限
            return func(*args, **kwargs)
        return app.restful.forbidden(msg="没有权限")

    return decorated_function


def admin_required(func):
    """ 校验当前用户是否有访问当前接口的权限 """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        from app.system.models.user import User
        if User.is_admin():
            return func(*args, **kwargs)
        return app.restful.forbidden(msg="没有权限")

    return decorated_function


def before_request_required():
    """ 解析token """
    parse_token(request.headers.get("X-Token"))
