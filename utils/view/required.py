# -*- coding: utf-8 -*-
import jwt
from flask import current_app as app, request, g, abort

from apps.enums import AuthType


def parse_access_token(access_token):
    """ 校验token是否过期，或者是否合法 """
    try:
        data = jwt.decode(access_token, app.config["SECRET_KEY"], algorithms=["HS256"])
        # 把用户数据存到g对象，方便后面使用
        g.user_id, g.user_name = data["id"], data["name"]
        g.api_permissions, g.business_list = data["api_permissions"], data["business_list"]
        return True
    except:
        return False


def check_login_and_permissions():
    """ 身份验证 """
    from apps.system.models.user import User

    # 根据请求路径判断是否需要身份验证 GET_/project/list
    request_path = request.path.split('/', 3)[-1]  # /api/apiTest/project/detail  =>  project/detail
    auth_type = app.url_required_map.get(f'{request.method}_/{request_path}')

    if auth_type != AuthType.not_auth:

        parse_access_token(request.headers.get("access-token"))

        if auth_type == AuthType.login:
            if not g.user_id:
                abort(401)

        elif auth_type == AuthType.permission:
            if User.is_not_admin() and request.path not in g.api_permissions:
                abort(403)

        elif auth_type == AuthType.admin:
            if User.is_not_admin():
                abort(403)
