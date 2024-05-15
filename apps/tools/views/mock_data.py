# -*- coding: utf-8 -*-
import json
import os
import time
import datetime
import importlib
import traceback

import requests
from flask import request, jsonify, current_app as app

from apps.api_test.model_factory import ApiMsg
from apps.tools.blueprint import tool
from utils.util.file_util import CALL_BACK_ADDRESS, FileUtil
from apps.assist.models.script import Script
from apps.config.models.config import Config
from utils.view import restful


def send_msg_by_webhook(msg_type, msg):
    """ 回调数据源成功时发送消息 """
    msg_format = {
        "msgtype": "text",
        "text": {
            "content": f'{msg}'
        }
    }
    try:
        print(
            f'{msg_type}发送企业微信：{requests.post(Config.get_callback_webhook(), json=msg_format).json()}')
    except Exception as error:
        print(f'向企业微信发送{msg_type}失败，错误信息：\n{error}')


def actions(action):
    """ 根据action执行不同的操作 """
    if action == "error":
        raise Exception("使用action参数触发的服务器内部错误")
    elif action == "time_out":
        time.sleep(40)


def get_auto_test_mock_data():
    """ 自动化测试模拟数据源
    1.json参数接收什么就返回什么
    2.args.action：查询字符串传参（非必传），在需要指定场景时使用，error、time_out、空
    {
        "action": "", # 指定事件，error为报错， time_out为等待40秒
        "is_async": "1",  # 判断数据源是同步还是异步
        "addr": "",  # 异步回调地址
        "token": "",  # 异步回调地址的token
    }
    """
    datas = request.json

    # action参数事件
    actions(datas.get("action"))

    # 根据是否有json参数判断是否为异步回调
    if datas and datas.get("is_async"):
        api_record_id, rating_request_id = datas.get("apiRecordId"), datas.get("ratingRequestId")
        try:
            # 发送异步回调
            res = requests.post(
                url=datas.get("addr", Config.get_data_source_callback_addr()),
                headers={"x-auth-token": datas.get("token", Config.get_data_source_callback_token())},
                json={
                    "applyType": 1,
                    "code": 200,
                    "apiRecordId": api_record_id,
                    "ratingRequestId": rating_request_id,
                    "message": "成功",
                    "content": datas,
                    "status": 200
                }
            )
            msg = {"message": "异步数据源回调成功", "status": 200, "apiRecordId": api_record_id, "data": res.json()}
        except Exception as error:
            msg = {"message": "异步数据源回调失败", "status": 500, "apiRecordId": api_record_id, "data": str(error)}
        return jsonify(msg)
    return jsonify(datas)


def get_sync_mock_data():
    """ 模拟数据源(同步) """
    return Config.get_sync_mock_data()


def call_back():
    """ 回调接口 """
    params, json_data, form_data = request.args.to_dict(), request.get_json(silent=True), request.form.to_dict()

    # 存回调数据
    name = f'callBack{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.json'
    FileUtil.save_file(os.path.join(CALL_BACK_ADDRESS, name), json_data or form_data or params)
    send_msg_by_webhook("回调结果", f"已收到回调数据，保存文件名：{name}")

    # 如果有配置返回数据，则返回回调数据，否则返回默认数据
    response = Config.get_call_back_response()
    if response:
        return jsonify(json.loads(response.value))

    return jsonify({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
        "status": 200,
        "message": "请求成功",
        "success": True,
        "data": name
    })


def mock_api():
    """ mock_api， 收到什么就返回什么 """
    params, json_data, form_data = request.args.to_dict(), request.get_json(silent=True), request.form.to_dict()
    return jsonify({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
        "status": 200,
        "message": "请求成功",
        "success": True,
        "data": json_data or form_data or params
    })


@tool.route("/mock/<script_name>", methods=['GET', 'POST', 'PUT', 'DELETE'])
def tool_mock_by_script(script_name):
    """ 根据python脚本文件处理mock机制 """
    script = Script.get_first(name=script_name)
    if not script:
        return app.restful.fail('mock脚本文件不存在')

    # 动态导入脚本
    try:
        script_file_name = f"mock_{script.name}"
        import_path = f'script_list.{script_file_name}'
        try:
            request_data = request.form.to_dict() or request.json
        except:
            request_data = {}
        FileUtil.save_mock_script_data(
            script_file_name,
            script.script_data,
            path=request.path,
            headers=dict(request.headers),
            query=request.args.to_dict(),
            body=request_data
        )
        script_obj = importlib.reload(importlib.import_module(import_path))
        return script_obj.result
    except Exception as e:
        return app.restful.fail(msg="脚本执行错误，请检查", result=traceback.format_exc())


@tool.route("/mock/auto-test", methods=['GET', 'POST', 'PUT', 'DELETE'])
def tool_mock_auto_test():
    """自动化测试模拟数据源"""
    return get_auto_test_mock_data()


@tool.route("/mock/sync", methods=['GET', 'POST', 'PUT', 'DELETE'])
def tool_mock_sync():
    return get_sync_mock_data()


@tool.route("/mock/call-back", methods=['GET', 'POST', 'PUT', 'DELETE'])
def tool_mock_call_back():
    """模拟回调"""
    return call_back()


@tool.route("/mock", methods=['GET', 'POST', 'PUT', 'DELETE'])
def tool_mock_api():
    """ 模拟接口处理，收到什么就返回什么 """
    return mock_api()


@tool.route("/mock/swagger/<path:api_addr>",
            methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def tool_mock_by_swagger(api_addr):
    """ 自定义mock接口返回 """
    if api_addr.startswith("/") is False:
        api_addr = f"/{api_addr}"
    query_set = ApiMsg.db.session.query(
        ApiMsg.id, ApiMsg.mock_response).filter(ApiMsg.addr == api_addr, ApiMsg.method == request.method).first()
    if not query_set or query_set[0] is None:
        query_set = ApiMsg.db.session.query(ApiMsg.mock_response).filter(ApiMsg.addr == api_addr).first()
        if not query_set:
            return restful.url_not_find()
        else:
            return restful.method_error()
    return query_set[1] or 'null'
