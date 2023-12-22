# -*- coding: utf-8 -*-
import uuid

from flask import request, g

from utils.logs.log import logger
from ..system.model_factory import User
from utils.view.required import check_login_and_permissions


def register_before_hook(app):
    """ 注册前置钩子函数，有请求时，会按函数所在位置，以从近到远的序顺序执行以下钩子函数 """

    @app.before_request
    def set_request_id():
        g.request_id = uuid.uuid4()

    @app.before_request
    def set_default_user():
        """ 设置一个默认用户 """
        if hasattr(g, "common_user_id") is False:
            current_user_query = User.db.session.query(User.id).filter(User.account == "common").first()
            g.common_user_id = current_user_query[0] if current_user_query else None

    @app.before_request
    def parse_request_ip():
        """ 获取用户ip """
        g.user_ip = request.headers.get("X-Forwarded-History") or request.headers.get(
            "X-Forwarded-From") or request.remote_addr

    @app.before_request
    def login_and_permission_required():
        """ 登录校验和权限校验 """
        check_login_and_permissions()  # 校验登录状态和权限

    @app.before_request
    def save_request_log():
        """ 打日志 """
        if request.method != "HEAD":
            try:
                request_data = request.args.to_dict() or request.form.to_dict() or request.json
            except:
                request_data = {}
            logger.info(
                f'【{g.get("request_id")}】【{g.get("user_name")}】【{g.user_ip}】【{request.method}】【{request.full_path}】: \n请求参数：{request_data}\n'
            )
