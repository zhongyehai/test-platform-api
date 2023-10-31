# -*- coding: utf-8 -*-
import platform
import traceback

from flask import current_app as _app, request

from app.system.models.errorRecord import SystemErrorRecord
from utils.message.sendReport import send_system_error


def register_errorhandler_hook(app):
    """ 注册异常捕获钩子函数 """

    @app.errorhandler(400)
    def forbidden_400(e):
        """ 捕获400异常 """
        return _app.restful.fail(e.description)

    @app.errorhandler(401)
    def forbidden_401(e):
        """ 捕获401的未登录异常 """
        return _app.restful.not_login()

    @app.errorhandler(403)
    def forbidden_403(e):
        """ 捕获403的未登录异常 """
        return _app.restful.forbidden(msg="没有权限")

    @app.errorhandler(404)
    def page_not_found(e):
        """ 捕获404的所有异常 """
        if request.method != "HEAD":
            _app.logger.exception(f'404错误url: {request.path}')
        return _app.restful.url_not_find(msg=f'接口 {request.path} 不存在')

    @app.errorhandler(Exception)
    def error_handler_500(e):
        """ 捕获所有服务器内部的异常，把错误发送到 即时达推送 的 系统错误 通道 """
        error = traceback.format_exc()
        try:
            _app.logger.exception(f'系统报错了:  \n\n url: {request.path} \n\n 错误详情: \n\n {error}')

            # 写数据库
            error_record = SystemErrorRecord().create({
                "url": request.path,
                "method": request.method,
                "headers": dict(request.headers),
                "params": request.args or {},
                "data_form": request.form or {},
                "data_json": request.json or {},
                "detail": error
            })

            # 发送即时通讯通知
            if platform.platform().startswith('Linux'):
                send_system_error(title=f'{_app.config["SECRET_KEY"]}报错通知，数据id：{error_record.id}', content=error)
        except:
            pass

        return _app.restful.error(f'服务器异常: {e}')