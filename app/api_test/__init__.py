# -*- coding: utf-8 -*-
import copy
import json

from flask import Blueprint, current_app, request
from flask_login import current_user

from app.utils.log import logger

api_test = Blueprint('apiTest', __name__)
api_test.logger = logger

from app.api_test.project import views
from app.api_test.module import views
from app.api_test.apiMsg import views
from app.api_test.sets import views
from app.api_test.case import views
from app.api_test.step import views
from app.api_test.task import views
from app.api_test.report import views
from app.api_test.func import views
from app.api_test.home import views


@api_test.before_request
def before_request():
    """ 前置钩子函数， 每个请求进来先经过此函数"""
    name = current_user.name if hasattr(current_user, 'name') else ''
    current_app.logger.info(
        f'[{request.remote_addr}] [{name}] [{request.method}] [{request.url}]: \n请求参数：{request.json}')


@api_test.after_request
def after_request(response_obj):
    """ 后置钩子函数，每个请求最后都会经过此函数 """
    if 'download' in request.path:
        return response_obj
    result = copy.copy(response_obj.response)
    if isinstance(result[0], bytes):
        result[0] = bytes.decode(result[0])
    # 减少日志数据打印，跑用例的数据均不打印到日志
    if 'apiMsg/run' not in request.path and 'report/run' not in request.path and 'report/list' not in request.path:
        current_app.logger.info(f'{request.method}==>{request.url}, 返回数据:{json.loads(result[0])}')
    return response_obj
