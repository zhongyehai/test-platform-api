# -*- coding: utf-8 -*-
import copy
import json
import traceback

import requests
from flask import current_app, request

from utils import restful
from app import create_app

app = create_app()


@app.before_request
def before_request():
    """ 前置钩子函数， 每个请求进来先经过此函数"""
    if request.method != 'HEAD':
        app.logger.info(
            f'【{request.remote_addr}】【{request.method}】【{request.url}】: \n请求参数：{request.json or request.form.to_dict() or request.args.to_dict()}'
        )


@app.after_request
def after_request(response_obj):
    """ 后置钩子函数，每个请求最后都会经过此函数 """
    if 'download' in request.path:
        return response_obj
    result = copy.copy(response_obj.response)
    if isinstance(result[0], bytes):
        result[0] = bytes.decode(result[0])
    # 减少日志数据打印，跑用例的数据均不打印到日志
    if 'apiMsg/run' not in request.path and 'report/run' not in request.path and 'report/list' not in request.path and request.method != 'HEAD':
        app.logger.info(f'{request.method}==>{request.url}, 返回数据:{json.loads(result[0])}')
    return response_obj


@app.errorhandler(404)
def page_not_found(e):
    """ 捕获404的所有异常 """
    # current_app.logger.exception(f'404错误url: {request.path}')
    return restful.url_not_find(msg=f'接口 {request.path} 不存在')


@app.errorhandler(Exception)
def error_handler(e):
    """ 捕获所有服务器内部的异常，把错误发送到 即时达推送 的 系统错误 通道 """
    error = traceback.format_exc()
    try:
        current_app.logger.error(f'系统出错了: {e}')
        requests.post(
            url=current_app.conf['error_push']['url'],
            json={
                'key': current_app.conf['error_push']['key'],
                'head': f'{current_app.conf["SECRET_KEY"]}报错了',
                'body': f'{error}'
            }
        )
    except:
        pass
    current_app.logger.exception(f'触发错误url: {request.path}\n{error}')
    return restful.error(f'服务器异常: {e}')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8024, debug=False)
