# -*- coding: utf-8 -*-
import json
import os.path

import requests
from flask import request, current_app as app

from app.assist.blueprint import assist
from app.assist.models.swagger import SwaggerPullLog
from app.baseView import LoginRequiredView
from app.api_test.models.project import ApiProject
from app.api_test.models.module import ApiModule
from app.api_test.models.api import ApiMsg
from utils.util.fileUtil import SWAGGER_FILE_ADDRESS, FileUtil
from app.baseModel import db


def get_swagger_data(swagger_addr):
    """ 获取swagger数据 """
    return requests.get(swagger_addr, verify=False).json()


def get_parsed_module(module_dict, project_id, controller_name, controller_tags):
    """ 获取已解析的模块 """

    # 已获取，则直接返回
    if controller_name in module_dict:
        return module_dict.get(controller_name)

    # 已解析，则直接获取
    module = ApiModule.get_first(project_id=project_id, controller=controller_name)
    if module:
        module_dict[module.name] = module
        return module

    # 未解析，则先解析并保存，再返回
    module = ApiModule().create({
        "project_id": project_id,
        "controller": controller_name,
        "name": controller_tags.get(controller_name, controller_name),  # 有tag就用tag，没有就用controller名字
        "num": ApiModule.get_insert_num(project_id=project_id)
    })
    module_dict[module.name] = module
    return module


def get_request_data_type(content_type):
    """ 判断请求参数类型 """
    if "json" in content_type or "raw" in content_type or "text/plain" in content_type:
        return "json"
    elif "data" in content_type:
        return "form"
    else:
        return "text"


def assert_is_update(api_msg, options):
    """ 判断参数是否需要更新 """
    header_update, params_update, data_json_update, data_form_update = False, False, False, False
    if "headers" in options and (api_msg.headers is None or json.loads(api_msg.headers)[0]["key"] is None):
        header_update = True
    if "query" in options and (api_msg.params is None or json.loads(api_msg.params)[0]["key"] is None):
        params_update = True
    if "data_json" in options and (api_msg.data_json is None or not json.loads(api_msg.data_json)):
        data_json_update = True
    if "data_form" in options and (api_msg.data_form is None or json.loads(api_msg.data_form)[0]["key"] is None):
        data_form_update = True
    return header_update, params_update, data_json_update, data_form_update


def update_obj(obj, field, data, is_update):
    """ 判断是否需要更新 """
    if is_update:
        setattr(obj, field, json.dumps(data, ensure_ascii=False, indent=4))


def parse_swagger2_args(api_msg, api_detail, swagger_data, options):
    """ 解析 swagger2 的参数 """
    update_header, update_params, update_data_json, update_data_form = assert_is_update(api_msg, options)  # 判断是否需要更新

    # 解析参数
    query = [{"key": None, "value": ""}]
    header = [{"key": None, "remark": None, "value": None}]
    form_data = [{"data_type": "", "key": None, "remark": None, "value": None}]
    json_data = {}
    for arg in api_detail.get("parameters", []):
        required = "必填" if arg.get("required") else "非必填"
        if update_params and arg["in"] == "query":  # 查询字符串参数
            query.insert(0, {
                "key": arg["name"],
                "value": f'{arg.get("description", "")} {arg["type"]} {required}'
            })
        elif update_header and arg["in"] == "header":  # 头部参数
            header.insert(0, {
                "key": arg["name"],
                "value": "",
                "remark": f'{arg.get("description", "")} {arg["type"]} {required}'
            })
        elif update_data_form and arg["in"] == "formData":  # form-data参数
            form_data.insert(0, {
                "key": arg["name"],
                "data_type": f'{arg.get("type")}',
                "value": "",
                "remark": f'{arg.get("description", "")} {required}'
            })
        elif update_data_json and arg["in"] == "body":  # json参数
            # properties = arg.get("schema", {}).get("properties", {})
            # for key, value in properties.items():
            #     json_data[key] = f"{value.get("description", "")} {value.get("type", "")}"
            ref = arg.get("schema", {}).get("$ref", "").split("/")[-1]
            properties = swagger_data.get("definitions", {}).get(ref, {}).get("properties", {})
            for key, value in properties.items():
                json_data[key] = f'{value.get("description", "")} {value.get("type", "")}'

    update_obj(api_msg, "headers", header, update_header)
    update_obj(api_msg, "params", query, update_params)
    update_obj(api_msg, "data_json", json_data, update_data_json)
    update_obj(api_msg, "data_form", form_data, update_data_form)


def parse_openapi3_parameters(parameters):
    """ 解析 openapi3 parameters字段 """
    headers, querys = {}, {}
    for arg_dict in parameters:
        required = "必填" if arg_dict.get("required") else "非必填"
        arg_value = f'{arg_dict.get("description", "")} {arg_dict.get("schema", {}).get("type")} {required}'

        if arg_dict["in"] == "header":  # 头部参数
            headers[arg_dict["name"]] = {"key": arg_dict["name"], "remark": None, "value": arg_value}
        elif arg_dict["in"] == "query":  # 查询字符串参数
            querys[arg_dict["name"]] = {"key": arg_dict["name"], "remark": None, "value": arg_value}
    return headers, querys


def parse_openapi3_request_body(request_body, data_models):
    """ 解析 openapi3 request_body字段 """
    json_data, form_data = {}, {}
    for content_type, content_detail in request_body.items():
        if content_type == "application/json":  # json 参数
            schema = content_detail.get("schema", {})
            if schema.get("type") == "array":  # 参数为数组
                data_model = schema.get("items", {}).get("$ref", "").split("/")[-1]  # 数据模型
            else:
                data_model = schema.get("$ref", "").split("/")[-1]  # 数据模型
            required_list = data_models.get(data_model, {}).get("required", [])
            model_data = data_models.get(data_model, {}).get("properties", {})
            if schema.get("type") == "array":  # 参数为数组
                json_data = [
                    {
                        key: f'{value.get("description", "")} {value.get("type", "")} {"必填" if key in required_list else "非必填"}'
                        for key, value in model_data.items()}
                ]
            else:
                json_data = {
                    key: f'{value.get("description", "")} {value.get("type", "")} {"必填" if key in required_list else "非必填"}'
                    for key, value in model_data.items()}
                # for key, value in model_data.items():
                #     json_data[key] = f"{value.get("description", "")} {value.get("type", "")} {"必填" if key in required_list else "非必填"}"

        elif content_type == "multipart/form-data":  # form-data 参数
            required_list = content_detail.get("schema", {}).get("required", [])  # 必传参数
            properties = content_detail.get("schema", {}).get("properties", {})  # 参数
            for field, items in properties.items():
                form_data[field] = {
                    "key": field,
                    "data_type": f'{items.get("type", "")}',
                    "value": "",
                    "remark": f'{items.get("description", "")} {"必填" if field in required_list else "非必填"}'
                }
        elif content_type == "x-www-form-urlencoded":  # x-www-form-urlencoded 参数
            pass
            # TODO 未拿到 x-www-form-urlencoded 相关的数据样例，暂不解析
            # required_list = content_detail.get("schema", {}).get("required", [])  # 必传参数
            # properties = content_detail.get("schema", {}).get("properties", {})  # 参数
            # for field, items in properties.items():
            #     form_data[field] = {
            #         "key": field,
            #         "data_type": f"{items.get("type", "")}",
            #         "value": "",
            #         "remark": f"{items.get("description", "")} {"必填" if field in required_list else "非必填"}"
            #     }

        elif content_type == "application/octet-stream":  # form-data 参数，传文件
            pass

        else:  # 其他参数
            print(f"content_type: {content_type}")
    return json_data, form_data


def parse_openapi3_response(ref_model, data_models):
    """ 解析 openapi3 response字段 """
    response_obj = {}
    data_model = data_models.get(ref_model, {})
    field_dict = data_model.get("properties", {})

    for field, field_detail in field_dict.items():
        if "$ref" not in field_detail:  # 字段为非对象
            response_obj[field] = f'{field_detail.get("description")} {field_detail.get("type")}'
        else:  # 字段为对象，递归解析
            sub_model = field_detail["$ref"].split("/")[-1]  # 数据模型
            response_obj[field] = {} if sub_model == ref_model else parse_openapi3_response(sub_model, data_models)

    return response_obj


def merge_dict(old_dict: dict, new_dict: dict):
    """ 合并字典，已有字段不改变 """
    if old_dict is None:
        return new_dict
    elif new_dict is None:
        return old_dict

    if isinstance(old_dict, str):
        old_dict = json.loads(old_dict)

    if isinstance(new_dict, str):
        new_dict = json.loads(new_dict)

    for key, value in old_dict.items():
        new_dict[key] = value
    return new_dict


def merge_data_json(old_dict: dict, new_dict: dict):
    """
    合并请求体
        如果都是字典，则合并
        如果都是列表，则返回原来的请求体
        如果数据类型不一致，则返回新的请求体
    """
    if isinstance(old_dict, str):
        old_dict = json.loads(old_dict)

    if isinstance(new_dict, str):
        new_dict = json.loads(new_dict)

    # 都是字典
    if isinstance(old_dict, dict) and isinstance(new_dict, dict):
        return merge_dict(old_dict, new_dict)

    # 都是列表，则不处理
    elif isinstance(old_dict, list) and isinstance(new_dict, list):
        return old_dict

    else:  # 新旧数据类型不一致，直接覆盖
        return new_dict


def dict_to_list(data: dict):
    """
    入参：
        {
            "a": {
                    "key": "a",
                    "value": 1,
                    "remark": "123"
                }
        }
    出参：
        [{
            "key": "a",
            "value": 1,
            "remark": "123"
        }]
    """
    if data is None:
        return [{"key": None, "remark": None, "value": None}]
    data_list = [value for key, value in data.items()]
    data_list.append({"key": None, "remark": None, "value": None})
    return data_list


def list_to_dict(data: list):
    """
    入参：
        [{
            "key": "a",
            "value": 1,
            "remark": "123"
        }]
    出参：
        {
            "a": {
                    "key": "a",
                    "value": 1,
                    "remark": "123"
                }
        }
    """
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, dict):
        return data
    return {} if data is None else {item["key"]: item for item in data if item["key"] is not None}


def parse_openapi3_args(db_api, swagger_api, data_models, options):
    """ 解析 openapi3 的参数 """
    headers, query, json_data, form_data, response_template = [], [], {}, [], {}

    swagger_headers_dict, swagger_query_dict = parse_openapi3_parameters(swagger_api.get("parameters", []))
    if "headers" in options:  # 请求头
        headers = dict_to_list(merge_dict(list_to_dict(db_api.headers), swagger_headers_dict))
    if "query" in options:  # 查询字符串参数
        query = dict_to_list(merge_dict(list_to_dict(db_api.params), swagger_query_dict))

    swagger_request_body_content = swagger_api.get("requestBody", {}).get("content", {})
    swagger_json_data, swagger_form_data = parse_openapi3_request_body(swagger_request_body_content, data_models)
    if "json" in options:  # json参数
        json_data = merge_data_json(db_api.data_json, swagger_json_data)
    if "form" in options:  # form-data参数
        form_data = dict_to_list(merge_dict(list_to_dict(db_api.data_form), swagger_form_data))

    if "response" in options:  # 响应
        ref_model = \
            swagger_api.get("responses",
                            {}).get("200",
                                    {}).get("content",
                                            {}).get("*/*", {}).get("schema", {}).get("$ref", "").split("/")[-1]  # 数据模型
        response_template = parse_openapi3_response(ref_model, data_models)

    # 更新api数据
    db_api.headers, db_api.params = db_api.dumps(headers), db_api.dumps(query)
    db_api.data_json, db_api.data_form = db_api.dumps(json_data), db_api.dumps(form_data)
    db_api.response = db_api.dumps(response_template)


class SwaggerPullView(LoginRequiredView):

    def post(self):
        """ 根据指定服务的swagger拉取所有数据 """
        options, project, module_dict = request.json.get("options"), ApiProject.get_first(id=request.json.get("id")), {}
        pull_log = SwaggerPullLog().create({"project_id": project.id})
        swagger_data = {}
        try:
            swagger_data = get_swagger_data(project.swagger)  # swagger数据
            status = swagger_data.get("status")
            if status and status >= 400:
                pull_log.pull_fail(project, swagger_data)
                fail_str = f"swagger数据拉取失败，响应结果为: \n{swagger_data}"
                app.logger.info(fail_str)
                return app.restful.fail(fail_str)
        except Exception as error:
            pull_log.pull_fail(project, swagger_data)
            fail_str = f"swagger数据拉取报错，结果为: \n{error.args}"
            app.logger.info(fail_str)
            return app.restful.fail(fail_str)
        pull_log.pull_success(project)

        # 解析已有的controller描述
        controller_tags = {tag["name"]: tag.get("description", tag["name"]) for tag in swagger_data.get("tags", [])}

        with db.auto_commit():

            add_list = []
            for api_addr, api_data in swagger_data["paths"].items():
                for api_method, swagger_api in api_data.items():
                    # 处理模块
                    controller_name = swagger_api.get("tags")[0] if swagger_api.get("tags") else "默认分组"
                    module = get_parsed_module(module_dict, project.id, controller_name, controller_tags)

                    # 处理接口
                    app.logger.info(f"解析接口地址：{api_addr}")
                    app.logger.info(f"解析接口数据：{swagger_api}")
                    api_name = swagger_api.get("summary", "接口未命名")
                    api_template = {
                        "deprecated": swagger_api.get("deprecated"),
                        "project_id": project.id,
                        "module_id": module.id,
                        "name": api_name,
                        "method": api_method.upper(),
                        "addr": api_addr,
                        "data_type": "json"
                    }

                    # 根据接口地址 获取/实例化 接口对象
                    if "{" in api_addr:  # URL中可能有参数化"/XxXx/xx/{batchNo}"
                        split_swagger_addr = api_addr.split("{")[0]
                        db_api = ApiMsg.query.filter(
                            ApiMsg.addr.like(f"%{split_swagger_addr}%"),
                            # ApiMsg.name == api_name,
                            ApiMsg.module_id == module.id
                        ).first() or ApiMsg()
                        if db_api.id and "$" in db_api.addr:  # 已经在测试平台修改过接口地址的路径参数
                            api_msg_addr_split = db_api.addr.split("$")
                            api_msg_addr_split[0] = split_swagger_addr
                            api_template["addr"] = "$".join(api_msg_addr_split)
                    else:
                        # db_api = ApiMsg.get_first(addr=api_addr, name=api_name, module_id=module.id) or ApiMsg()
                        db_api = ApiMsg.get_first(addr=api_addr, module_id=module.id) or ApiMsg()

                    # swagger2和openapi3格式不一样，处理方法不一样
                    if "2" in swagger_data.get("swagger", ""):  # swagger2
                        content_type = swagger_api.get("consumes", ["json"])[0]  # 请求数据类型
                        parse_swagger2_args(db_api, swagger_api, swagger_data, options)  # 处理参数
                    elif "3" in swagger_data.get("openapi", ""):  # openapi 3
                        content_types = swagger_api.get("requestBody", {}).get("content", {"application/json": ""})
                        content_type = list(content_types.keys())[0]
                        data_models = swagger_data.get("components", {}).get("schemas", {})
                        parse_openapi3_args(db_api, swagger_api, data_models, options)  # 处理参数

                    # 处理请求参数类型
                    api_template["data_type"] = get_request_data_type(content_type)

                    # 新的接口则赋值
                    for key, value in api_template.items():
                        if hasattr(db_api, key):
                            setattr(db_api, key, value)

                    if db_api.id is None:  # 没有id，则为新增
                        db_api.num = ApiMsg.get_insert_num(module_id=module.id)
                        add_list.append(db_api)

            db.session.add_all(add_list)

            # 同步完成后，保存原始数据
            swagger_file = os.path.join(SWAGGER_FILE_ADDRESS, f"{project.id}.json")
            FileUtil.delete_file(swagger_file)
            FileUtil.save_file(swagger_file, swagger_data)

        return app.restful.success("数据拉取并更新完成")


assist.add_url_rule("/swagger/pull", view_func=SwaggerPullView.as_view("SwaggerPullView"))
