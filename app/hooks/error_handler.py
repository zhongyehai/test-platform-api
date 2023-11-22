# -*- coding: utf-8 -*-
import platform
import re
import traceback

import pymysql
from flask import current_app as _app, request, g
from pydantic import ValidationError
from pymysql import err as pymysql_err

from app.system.models.error_record import SystemErrorRecord
from utils.message.send_report import send_system_error
import config


def register_errorhandler_hook(app):
    """ 注册异常捕获钩子函数 """

    @app.errorhandler(400)
    def forbidden_400(e):
        """ 捕获400异常 """
        return _app.restful.fail(e.description)

    @app.errorhandler(401)
    def forbidden_401(e):
        """ 捕获401的未登录异常 """
        return _app.restful.not_login(
            _app.config["OSS"].front_redirect_addr if _app.config["AUTH_TYPE"] == "OSS" else None)

    @app.errorhandler(403)
    def forbidden_403(e):
        """ 捕获403的权限不足异常 """
        return _app.restful.forbidden(msg="没有权限")

    @app.errorhandler(404)
    def page_not_found(e):
        """ 捕获404的所有异常 """
        if request.method != "HEAD":
            _app.logger.exception(f'404错误url: {request.path}')
        return _app.restful.url_not_find(msg=f'接口 {request.path} 不存在')

    @app.errorhandler(ValidationError)
    def pydantic_validation_error(exc):
        """ pydantic数据校验不通过
        {
            'input': {
                'business_id': 16, 'id': None, 'manager': 1, 'name': '123', 'script_list': []
            },
            'loc': ('swagger',),
            'msg': 'Field required',
            'type': 'missing',
            'url': 'https://errors.pydantic.dev/2.4/v/missing'
        }
        """
        error = exc.errors()[0]
        request_data, filed_name, error_type, msg = error["input"], error["loc"][-1], error["type"], error["msg"]
        filed_title = g.current_from.get_filed_title(filed_name)
        if "type" in error_type or error_type == "int_parsing":  # 数据类型错误
            return _app.restful.fail(f'{filed_title} 数据类型错误')

        elif "required" in msg:  # 必传字段
            return _app.restful.fail(f'{filed_title} 必传')

        elif "value_error" in error_type:  # 数据验证不通过
            # 'Value error, 服务名【xxxx】已存在'
            return _app.restful.fail(msg.split(', ', 1)[1])

        elif "enum" in error_type:  # 枚举错误
            return _app.restful.fail(f'{filed_title} 枚举错误：{msg}')

        elif "max_length" in error_type:  # 数据长度超长
            return _app.restful.fail(f'{request_data[filed_name]} 长度超长，最多{error["ctx"]["limit_value"]}位')

        elif "min_length" in error_type:  # 数据长度超长
            return _app.restful.fail(f'{request_data[filed_name]} 长度不够，最少{error["ctx"]["limit_value"]}位')
        # TODO 其他校验类型

    @app.errorhandler(Exception)
    def error_handler_500(e):
        """ 捕获所有服务器内部的异常，把错误发送到 即时达推送 的 系统错误 通道 """
        try:
            original = getattr(e, "orig", None)
            if original:
                error_code, error_msg = getattr(original, "args", None)
                if "Duplicate" in error_msg:  # 数据重复
                    filed_value = re.findall("'(.+?)'", error_msg)[0]
                    return _app.restful.fail(f'{filed_value} 已存在')
            # TODO 更多数据库异常捕获
        except:
            pass
        error = traceback.format_exc()
        try:
            _app.logger.exception(f'系统报错了:  \n\n url: {request.path} \n\n 错误详情: \n\n {error}')

            # 写数据库
            error_record = SystemErrorRecord.model_create({
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
                send_system_error(title=f'{config.secret_key}报错通知，数据id：{error_record.id}', content=error)
        except:
            pass

        return _app.restful.error(f'服务器异常: {e}')
