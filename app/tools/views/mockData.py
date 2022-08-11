# -*- coding: utf-8 -*-

import io
import json
import os
import time
import datetime

import requests
from flask import request, jsonify

from app.tools import tool
from utils.globalVariable import CALL_BACK_ADDRESS
from app.config.models.config import Config


def send_msg_by_webhook(msg_type, msg):
    """ 回调数据源成功时发送消息 """
    msg_format = {
        "msgtype": "text",
        "text": {
            "content": f"{msg}"
        }
    }
    try:
        print(
            f'{msg_type}发送企业微信：{requests.post(Config.get_callback_webhook(), json=msg_format).json()}')
    except Exception as error:
        print(f'向企业微信发送{msg_type}失败，错误信息：\n{error}')


def actions(action):
    """ 根据action执行不同的操作 """
    if action == 'error':
        raise Exception('使用action参数触发的服务器内部错误')
    elif action == 'time_out':
        time.sleep(40)


@tool.route('/mockData/autoTest', methods=['GET', 'POST'])
def return_auto_test_mock_data_not_login_required():
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
    actions(datas.get('action'))

    # 根据是否有json参数判断是否为异步回调
    if datas and datas.get('is_async'):
        api_record_id, rating_request_id = datas.get('apiRecordId'), datas.get('ratingRequestId')
        try:
            # 发送异步回调
            res = requests.post(
                url=datas.get('addr', Config.get_data_source_callback_addr()),
                headers={'x-auth-token': datas.get('token', Config.get_data_source_callback_token())},
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


@tool.route('/mockData/common', methods=['GET', 'POST'])
def return_mock_data_not_login_required():
    """ 模拟数据源
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
    actions(datas.get('action'))

    # 根据是否有json参数判断是否为异步回调
    if datas and datas.get('is_async'):
        api_record_id, rating_request_id = datas.get('apiRecordId'), datas.get('ratingRequestId')
        try:
            # 发送异步回调
            res = requests.post(
                url=Config.get_data_source_callback_addr(),
                headers={'x-auth-token': Config.get_data_source_callback_token()},
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
        send_msg_by_webhook('数据源回调结果', msg)
        return jsonify(msg)
    send_msg_by_webhook('数据源回调结果', {"message": "同步数据源回调成功", "status": 200})
    return jsonify(datas)


@tool.route('/callBack', methods=['GET', 'POST'])
def call_back_not_login_required():
    """ 回调接口 """
    params, json_data, form_data = request.args.to_dict(), request.get_json(silent=True), request.form.to_dict()

    # 存回调数据
    name = f'callBack{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.json'
    with io.open(os.path.join(CALL_BACK_ADDRESS, name), 'w', encoding='utf-8') as call_back_file:
        json.dump(json_data or form_data or params, call_back_file, ensure_ascii=False)
    send_msg_by_webhook('回调结果', f'已收到回调数据，保存文件名：{name}')

    # 如果有配置返回数据，则返回回调数据，否则返回默认数据
    response = Config.get_call_back_response()
    if response:
        return jsonify(json.loads(response.value))

    return jsonify({
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
        "status": 200,
        "message": "请求成功",
        "data": name})


@tool.route('/mock', methods=['GET', 'POST'])
def mock_api_not_login_required():
    """ mock_api， 收到什么就返回什么 """
    params, json_data, form_data = request.args.to_dict(), request.get_json(silent=True), request.form.to_dict()
    return jsonify({
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
        "status": 200,
        "message": "请求成功",
        "data": json_data or form_data or params
    })
