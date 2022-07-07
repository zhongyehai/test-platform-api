# -*- coding: utf-8 -*-

from flask import views

from .utils.required import login_required, admin_required
from .utils.jsonUtil import JsonUtil


class BaseMethodView(views.MethodView, JsonUtil):
    """ 继承views.MethodView, 并使每个继承此基类MethodView的类视图默认带上 login_required登录校验 """
    decorators = [login_required]


class AdminMethodView(BaseMethodView):
    """ 管理员权限校验 """
    decorators = [admin_required, login_required]  # 后面的装饰器先执行
