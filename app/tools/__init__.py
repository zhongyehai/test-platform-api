import copy
import json

from flask import Blueprint, current_app as app, request, g

from app.utils.log import logger

tool = Blueprint('tool', __name__)
tool.logger = logger

from app.tools import examination
from app.tools import makeUser
from app.tools import mockData


@tool.before_request
def before_request():
    """ 前置钩子函数， 每个请求进来先经过此函数"""
    name = g.user_name if hasattr(g, 'user_name') else ''
    app.logger.info(
        f'【{request.remote_addr}】【{name}】【{request.method}】【{request.url}】: \n请求参数：{request.json or request.form.to_dict() or request.args.to_dict()}'
    )


@tool.after_request
def after_request(response_obj):
    """ 后置钩子函数，每个请求最后都会经过此函数 """
    if 'download' in request.path:
        return response_obj
    result = copy.copy(response_obj.response)
    if isinstance(result[0], bytes):
        result[0] = bytes.decode(result[0])
    # 减少日志数据打印，跑用例的数据均不打印到日志
    if 'apiMsg/run' not in request.path and 'report/run' not in request.path and 'report/list' not in request.path:
        app.logger.info(f'{request.method}==>{request.url}, 返回数据:{json.loads(result[0])}')
    return response_obj
