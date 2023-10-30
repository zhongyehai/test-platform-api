# -*- coding: utf-8 -*-
from flask import request, g

from app.config.models.config import Config
from app.system.models.userOperationLog import UserOperationLog
from utils.view.required import check_login_and_permissions


def register_before_hook(app):
    """ 注册前置钩子函数，有请求时，会按函数所在位置，以从近到远的序顺序执行以下钩子函数 """

    @app.before_first_request
    def set_config():
        """ 第一次请求时，获取并初始化配置 """
        # 获取分页信息
        pagination = Config.get_pagination_size()
        app.config["page_num"] = pagination["page_num"]
        app.config["page_size"] = pagination["page_size"]

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
    def save_requests_by_log():
        """ 打日志 """
        if request.method != "HEAD":
            request_data = request.json or request.form.to_dict() or request.args.to_dict()
            app.logger.info(
                f'【{g.get("user_name")}】【{g.user_ip}】【{request.method}】【{request.url}】: \n请求参数：{request_data}\n'
            )

    # @app.before_request
    # def save_requests_by_db():
    #     """ 存操作日志 """
    #     if request.method in ("POST", "PUT", "DELETE"):
    #         UserOperationLog().create({
    #             "ip": g.user_ip,
    #             "url": request.path,
    #             "method": request.method,
    #             "headers": dict(request.headers),
    #             "params": request.args or {},
    #             "data_form": request.form or {},
    #             "data_json": request.json or {}
    #         })
