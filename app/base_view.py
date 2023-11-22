# -*- coding: utf-8 -*-
from flask import Blueprint as FlaskBlueprint

from app.enums import AuthType

url_required_map = {}


class Blueprint(FlaskBlueprint):

    def get(self, path, *args, auth_type=AuthType.not_auth, **kwargs):
        """ 不需要身份验证 """
        url_required_map[f'GET_{path}'] = auth_type  # # 记录此 请求方法+路径 的身份验证类型
        return super(Blueprint, self).route(path, methods=["GET"], **kwargs)

    def login_get(self, path, *args, **kwargs):
        """ 登录验证的接口 """
        return self.get(path, auth_type=AuthType.login, *args, **kwargs)

    def permission_get(self, path, *args, **kwargs):
        """ 需要接口权限验证的接口 """
        return self.get(path, auth_type=AuthType.permission, *args, **kwargs)

    def admin_get(self, path, *args, **kwargs):
        """ 管理员验证的接口 """
        return self.get(path, auth_type=AuthType.admin, *args, **kwargs)

    def post(self, path, *args, auth_type=AuthType.not_auth, **kwargs):
        """ 不需要身份验证 """
        url_required_map[f'POST_{path}'] = auth_type  # # 记录此 请求方法+路径 的身份验证类型
        return super(Blueprint, self).route(path, methods=["POST"], **kwargs)

    def login_post(self, path, *args, **kwargs):
        """ 登录验证的接口 """
        return self.post(path, auth_type=AuthType.login, *args, **kwargs)

    def permission_post(self, path, *args, **kwargs):
        """ 需要接口权限验证的接口 """
        return self.post(path, auth_type=AuthType.permission, *args, **kwargs)

    def admin_post(self, path, *args, **kwargs):
        """ 管理员验证的接口 """
        return self.post(path, auth_type=AuthType.admin, *args, **kwargs)

    def put(self, path, *args, auth_type=AuthType.not_auth, **kwargs):
        """ 不需要身份验证 """
        url_required_map[f'PUT_{path}'] = auth_type  # # 记录此 请求方法+路径 的身份验证类型
        return super(Blueprint, self).route(path, methods=["PUT"], **kwargs)

    def login_put(self, path, *args, **kwargs):
        """ 登录验证的接口 """
        return self.put(path, auth_type=AuthType.login, *args, **kwargs)

    def permission_put(self, path, *args, **kwargs):
        """ 需要接口权限验证的接口 """
        return self.put(path, auth_type=AuthType.permission, *args, **kwargs)

    def admin_put(self, path, *args, **kwargs):
        """ 管理员验证的接口 """
        return self.put(path, auth_type=AuthType.admin, *args, **kwargs)

    def delete(self, path, *args, auth_type=AuthType.not_auth, **kwargs):
        """ 不需要身份验证 """
        url_required_map[f'DELETE_{path}'] = auth_type  # 记录此 请求方法+路径 的身份验证类型
        return super(Blueprint, self).route(path, methods=["DELETE"], **kwargs)

    def login_delete(self, path, *args, **kwargs):
        """ 登录验证的接口 """
        return self.delete(path, auth_type=AuthType.login, *args, **kwargs)

    def permission_delete(self, path, *args, **kwargs):
        """ 需要接口权限验证的接口 """
        return self.delete(path, auth_type=AuthType.permission, *args, **kwargs)

    def admin_delete(self, path, *args, **kwargs):
        """ 管理员验证的接口 """
        return self.delete(path, auth_type=AuthType.admin, *args, **kwargs)
