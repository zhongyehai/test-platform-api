#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/12/31 11:32
# @Author : ZhongYeHai
# @Site : 
# @File : swagger.py
# @Software: PyCharm
import json
import os.path

import requests
from flask import request

from app.test_work import test_work
from app.api_test.project.models import ApiProject
from app.api_test.module.models import ApiModule
from app.api_test.apiMsg.models import ApiMsg
from app.utils import restful
from app.utils.globalVariable import SWAGGER_FILE_ADDRESS
from app.utils.required import login_required
from app.baseModel import db


def get_swagger_data(swagger_addr):
    """ 获取swagger数据 """
    return requests.get(swagger_addr, verify=False).json()


def get_parsed_module(module_list, project_id, module_name):
    """ 获取已解析的模块 """

    # 已获取，则直接返回
    if module_name in module_list:
        return module_list.get(module_name)

    # 已解析，则直接获取
    module = ApiModule.get_first(project_id=project_id, name=module_name)
    if module:
        module_list[module.name] = module
        return module

    # 未解析，则先解析并保存，再返回
    module = ApiModule().create(
        {'project_id': project_id, 'name': module_name, 'num': ApiModule.get_insert_num(project_id=project_id)})
    module_list[module.name] = module
    return module


def get_request_data_type(content_type):
    """ 判断请求参数类型 """
    if 'json' in content_type or 'raw' in content_type or 'text/plain' in content_type:
        return 'json'
    elif 'data' in content_type:
        return 'form'
    else:
        return 'xml'


def assert_is_update(api_msg):
    """ 判断参数是否需要更新 """
    # 判断是否需要更新
    header_update, params_update, data_json_update, data_form_update = False, False, False, False
    if not api_msg.headers or not json.loads(api_msg.headers)[0]['key']:
        header_update = True
    if not api_msg.params or not json.loads(api_msg.params)[0]['key']:
        params_update = True
    if not api_msg.data_json or not json.loads(api_msg.data_json):
        data_json_update = True
    if not api_msg.data_form or not json.loads(api_msg.data_form)[0]['key']:
        data_form_update = True
    return header_update, params_update, data_json_update, data_form_update


def update_obj(obj, field, data, is_update):
    """ 判断是否需要更新 """
    if is_update:
        setattr(obj, field, json.dumps(data, ensure_ascii=False, indent=4))


def parse_swagger2_args(api_msg, api_detail, swagger_data):
    """ 解析 swagger2 的参数 """
    header_update, params_update, data_json_update, data_form_update = assert_is_update(api_msg)  # 判断是否需要更新

    # 解析参数
    query = [{"key": None, "value": ''}]
    header = [{"key": None, "remark": None, "value": None}]
    form_data = [{"data_type": '', "key": None, "remark": None, "value": None}]
    json_data = {}
    for arg in api_detail.get('parameters', []):
        required = "必填" if arg.get('required') else "非必填"
        if arg['in'] == 'query' and params_update:  # 查询字符串参数
            query.insert(0, {
                "key": arg['name'],
                "value": f"{arg.get('description', '')} {arg['type']} {required}"
            })
        # 若要同步头部信息，则打开此处的注释即可
        # elif arg['in'] == 'header' and header_update:  # 头部参数
        #     header.insert(0, {
        #         "key": arg['name'],
        #         "value": "",
        #         "remark": f"{arg.get('description', '')} {arg['type']} {required}"
        #     })
        elif arg['in'] == 'formData' and data_form_update:  # form-data参数
            form_data.insert(0, {
                "key": arg['name'],
                "data_type": f"{arg.get('type')}",
                "value": "",
                "remark": f"{arg.get('description', '')} {required}"
            })
        elif arg['in'] == 'body' and data_json_update:  # json参数
            # properties = arg.get('schema', {}).get('properties', {})
            # for key, value in properties.items():
            #     json_data[key] = f"{value.get('description', '')} {value.get('type', '')}"
            ref = arg.get('schema', {}).get('$ref', '').split('/')[-1]
            properties = swagger_data.get('definitions', {}).get(ref, {}).get('properties', {})
            for key, value in properties.items():
                json_data[key] = f"{value.get('description', '')} {value.get('type', '')}"

    update_obj(api_msg, 'headers', header, header_update)
    update_obj(api_msg, 'params', query, params_update)
    update_obj(api_msg, 'data_json', json_data, data_json_update)
    update_obj(api_msg, 'data_form', form_data, data_form_update)


def parse_openapi3_args(api_msg, api_detail, models):
    """ 解析 openapi3 的参数 """
    header_update, params_update, data_json_update, data_form_update = assert_is_update(api_msg)  # 判断是否需要更新

    # 解析参数
    query = [{"key": None, "value": ''}]
    header = [{"key": None, "remark": None, "value": None}]
    form_data = [{"data_type": '', "key": None, "remark": None, "value": None}]
    json_data = {}

    # TODO 头部参数和更多参数

    # 查询字符串参数
    if params_update:
        for arg in api_detail.get('parameters', []):
            required = "必填" if arg.get('required') else "非必填"
            if arg['in'] == 'query':
                query.insert(0, {
                    "key": arg['name'],
                    "value": f"{arg.get('description', '')} {arg.get('schema', {}).get('type')} {required}"
                })

    # 请求体
    request_body_content = api_detail.get('requestBody', {}).get('content', {})
    for content_type, detail in request_body_content.items():
        if content_type == 'application/json':  # json 参数
            if data_json_update:
                data_model = detail.get('schema', {}).get('$ref', '').split('/')[-1]  # 数据模型
                model_data = models.get(data_model, {}).get('properties', {})
                for key, value in model_data.items():
                    json_data[key] = f"{value.get('description', '')} {value.get('type', '')}"

        elif content_type == 'multipart/form-data':  # form-data 参数
            required_list = detail.get('schema', {}).get('required', [])  # 必传参数
            properties = detail.get('schema', {}).get('properties', {})  # 参数
            for field, items in properties.items():
                form_data.insert(0, {
                    "key": field,
                    "data_type": f"{items.get('type', '')}",
                    "value": "",
                    "remark": f"{items.get('description', '')} {'必填' if field in required_list else '非必填'}"
                })
        elif content_type == 'application/octet-stream':  # form-data 参数，传文件
            pass

        else:  # 其他参数
            print(f'content_type: {content_type}')

    update_obj(api_msg, 'headers', header, header_update)
    update_obj(api_msg, 'params', query, params_update)
    update_obj(api_msg, 'data_json', json_data, data_json_update)
    update_obj(api_msg, 'data_form', form_data, data_form_update)


@test_work.route('/swagger/pull', methods=['POST'])
@login_required
def swagger_pull():
    """ 根据指定服务的swagger拉取所有数据 """
    project, module_list = ApiProject.get_first(id=request.json.get('id')), {}

    try:
        swagger_data = get_swagger_data(project.swagger)  # swagger数据
    except Exception as error:
        test_work.logger.error(error)
        return restful.error('数据拉取失败，详见日志')

    with db.auto_commit():
        add_list = []
        for api_addr, api_data in swagger_data['paths'].items():
            for api_method, api_detail in api_data.items():
                tags = api_detail.get('tags')[0] if api_detail.get('tags') else '默认分组'
                module = get_parsed_module(module_list, project.id, tags)
                test_work.logger.info(f'解析接口地址：{api_addr}')
                test_work.logger.info(f'解析接口数据：{api_detail}')
                api_name = api_detail.get('summary', '接口未命名')
                format_data = {
                    'project_id': project.id,
                    'module_id': module.id,
                    'name': api_name,
                    'method': api_method.upper(),
                    'addr': api_addr,
                    'data_type': 'json'
                }
                content_type = json

                # 根据接口地址获取接口对象
                if '{' in api_addr:  # URL中可能有参数化"/XxXx/xx/{batchNo}"
                    split_swagger_addr = api_addr.split('{')[0]
                    api_msg = ApiMsg.query.filter(
                        ApiMsg.addr.like('%' + split_swagger_addr + '%'),
                        ApiMsg.name == api_name,
                        ApiMsg.module_id == module.id
                    ).first() or ApiMsg()
                    if api_msg.id and '$' in api_msg.addr:  # 已经在测试平台修改过接口地址的参数
                        api_msg_addr_split = api_msg.addr.split('$')
                        api_msg_addr_split[0] = split_swagger_addr
                        format_data['addr'] = '$'.join(api_msg_addr_split)
                else:
                    api_msg = ApiMsg.get_first(addr=api_addr, name=api_name, module_id=module.id) or ApiMsg()

                if '2' in swagger_data.get('swagger', ''):  # swagger2
                    content_type = api_detail.get('consumes', ['json'])[0]  # 请求数据类型
                    parse_swagger2_args(api_msg, api_detail, swagger_data)  # 处理参数
                elif '3' in swagger_data.get('openapi', ''):  # openapi 3
                    content_types = api_detail.get('requestBody', {}).get('content', {'application/json': ''})
                    content_type = list(content_types.keys())[0]
                    models = swagger_data.get('components', {}).get('schemas', {})
                    parse_openapi3_args(api_msg, api_detail, models)  # 处理参数
                # 处理请求参数类型
                format_data['data_type'] = get_request_data_type(content_type)

                # 赋值
                for key, value in format_data.items():
                    if hasattr(api_msg, key):
                        setattr(api_msg, key, value)

                if api_msg.id is None:  # 没有id，则为新增
                    api_msg.num = ApiMsg.get_insert_num(module_id=module.id)
                    add_list.append(api_msg)

        db.session.add_all(add_list)

        # 同步完成后，保存原始数据
        swagger_file = os.path.join(SWAGGER_FILE_ADDRESS, f'{project.id}.json')
        if os.path.exists(swagger_file):
            os.remove(swagger_file)
        with open(swagger_file, 'w', encoding='utf8') as fp:
            json.dump(swagger_data, fp, ensure_ascii=False, indent=4)

    return restful.success('数据拉取并更新完成')
