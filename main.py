# -*- coding: utf-8 -*-

from app import create_app
import traceback

import requests
from flask import current_app, request

from app.utils import restful

app = create_app()


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
