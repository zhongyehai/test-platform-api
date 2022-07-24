# -*- coding: utf-8 -*-

from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask import current_app as app, request, g

from utils import restful


def parse_token(token):
    """ 校验token是否过期，或者是否合法 """
    try:
        from app.ucenter.models.user import User
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
        return func(*args, **kwargs) if parse_token(request.headers.get('X-Token')) else restful.fail('登录超时,请重新登录')

    return decorated_view


def permission_required(permission_name):
    """ 校验当前用户是否有访问当前接口的权限 """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            from app.ucenter.models.user import User
            user = User.get_first(id=g.user_id)
            return restful.forbidden('没有该权限') if not user.can(permission_name) else func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(func):
    """ 校验是否为管理员权限 """
    return permission_required('ADMINISTER')(func)
