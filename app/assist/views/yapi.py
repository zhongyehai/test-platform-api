# -*- coding: utf-8 -*-
import json
import os
import re

import requests
from flask import request, send_from_directory, g, current_app as app

from app.api_test.models.api import ApiMsg
from app.api_test.models.module import ApiModule
from app.api_test.models.project import ApiProject, ApiProjectEnv
from app.assist.blueprint import assist
from app.assist.models.yapi import YapiProject, YapiModule, YapiApiMsg, YapiDiffRecord
from app.baseModel import db
from app.config.models.config import Config
from utils.util.fileUtil import DIFF_RESULT, FileUtil
from utils.makeData.makeXmind import make_xmind
from utils.message.sendReport import send_diff_api_message


class LoginRequiredView:
    pass

def assert_coding_format(data):
    """ 判断字符串是否为utf-8 """
    return "�" not in data


def pop_ignore(data_list, ignore_list, key):
    """ 过滤要排除的项 """
    for index, project in enumerate(data_list):
        for ignore in ignore_list:
            if ignore and ignore in project[key]:
                data_list.pop(index)
    return data_list


def get_module_data(db_module_dict, cat_id):
    """ 获取原始模块数据 """
    db_module = db_module_dict.get(cat_id)
    if not db_module:
        db_module = YapiModule.get_first(yapi_id=cat_id)
        db_module_dict[db_module.yapi_id] = db_module
    return db_module


def parse_path(api_msg, yapi_api):
    """ 接口地址处理，接口地址中可能有参数化 """
    api_msg.addr = yapi_api["path"]
    if api_msg.id:
        if "{" in yapi_api["path"]:
            split_api_msg_addr = api_msg.addr.split("$")
            split_api_msg_addr[0] = yapi_api["path"].split("{")[0]
            api_msg.addr = "$".join(split_api_msg_addr)
    # if split_api_msg_addr.__len__() > 1:
    #     api_msg.addr = yapi_api["path"].split("{")[0] + "$" + split_api_msg_addr[1]


def parse_header(api_msg, yapi_api):
    """ 处理头部信息 """
    if api_msg.headers and json.loads(api_msg.headers) and json.loads(api_msg.headers)[0].get("key"):
        return

    # 若要同步头部信息，则注释此行代码，打开下面的注释即可
    api_msg.headers = json.dumps([{"key": None, "remark": None, "value": None}], ensure_ascii=False, indent=4)

    # req_headers = yapi_api.get("req_headers", [])
    # data = [{"key": header.get("name"), "remark": None, "value": header.get("value")} for header in req_headers]
    # data.extend([{"key": None, "remark": None, "value": None}])
    # api_msg.headers = json.dumps(data, ensure_ascii=False, indent=4)


def parse_query(api_msg, yapi_api):
    """ 处理查询字符串参数 """
    if api_msg.params and json.loads(api_msg.params) and json.loads(api_msg.params)[0].get("key"):
        return
    data = [{
        "key": query["name"],
        "value": f'{query.get("required", "")} {"必填" if query.get("desc") == "1" else "非必填"}'
    } for query in yapi_api.get("req_query", [])]
    data.extend([{"key": None, "value": ""}])
    api_msg.params = json.dumps(data, ensure_ascii=False, indent=4)


def parse_data_type(api_msg, yapi_api):
    """ 处理请求数据类型 """
    data_type = yapi_api.get("req_body_type", "json")
    api_msg.data_type = "json" if data_type in ["row", "json"] else data_type


def parse_json(api_msg, yapi_api):
    """ 处理json参数, 继承已有的json参数 """
    default = {}

    if api_msg.data_json and json.loads(api_msg.data_json):
        default = json.loads(api_msg.data_json)

    if yapi_api.get("req_body_type", "") in ["json", "raw"]:
        req_body_other = yapi_api.get("req_body_other", "{}")
        if req_body_other:
            body_obj = json.loads(req_body_other)
            if body_obj.get("type") == "object":  # 请求体为json
                json_data = {}
                for key, items in body_obj.get("properties", {}).items():
                    json_data.setdefault(key, f'描述：{items.get("description")}, 类型：{items.get("type")}')
                json_data.update(default)
                api_msg.data_json = json.dumps(json_data, ensure_ascii=False, indent=4)
                return

            elif body_obj.get("type") == "array":  # 请求体为数组
                json_data = {}
                for key, items in body_obj.get("items", {}).get("properties", {}).items():
                    json_data.setdefault(key, f'描述：{items.get("description")}, 类型：{items.get("type")}')
                if isinstance(default, list):
                    json_data.update(default[0])
                api_msg.data_json = json.dumps([json_data], ensure_ascii=False, indent=4)
                return

    api_msg.data_json = json.dumps(default, ensure_ascii=False, indent=4)


def parse_form(api_msg, yapi_api):
    """ 解析form参数 """
    if api_msg.data_form and json.loads(api_msg.data_form) and json.loads(api_msg.data_form)[0].get("key"):
        return
    default = [{"data_type": "", "key": None, "remark": None, "value": None}]
    if yapi_api.get("req_body_type", "") == "form":
        default = [
            {
                "data_type": "file" if form.get("type") and form.get("type") == "file" else "string",
                "key": form.get("name"),
                "remark": form.get("desc"),
                "value": None
            } for form in yapi_api.get("req_body_form", [])]
        default.extend([{"data_type": "", "key": None, "remark": None, "value": None}])
    api_msg.data_form = json.dumps(default, ensure_ascii=False, indent=4)


def update_project(yapi_project):
    """ yapi 的服务信息更新到测试平台的服务 """

    with db.auto_commit():
        # 存服务原始信息
        original_yapi_project = YapiProject.get_first(yapi_id=yapi_project["_id"]) or YapiProject()
        original_yapi_project.yapi_group = yapi_project["group_id"]
        original_yapi_project.yapi_name = yapi_project["name"]
        original_yapi_project.yapi_id = yapi_project["_id"]
        original_yapi_project.yapi_data = json.dumps(yapi_project, ensure_ascii=False, indent=4)  # 把原始服务信息存下来
        if not original_yapi_project.id:
            db.session.add(original_yapi_project)
        app.logger.info(f'原始yapi服务信息: \n{yapi_project}')

        # 存解析后服务数据
        project = ApiProject.get_first(yapi_id=yapi_project["_id"]) or ApiProject()
        project.name = yapi_project["name"]
        project.yapi_id = yapi_project["_id"]
        data_type = None  # 标识数据是新增还是修改
        if not project.id:
            data_type = "add"
            db.session.add(project)
    if data_type == "add":
        ApiProjectEnv.create_env(project.id)  # 创建环境
    app.logger.info(f'解析yapi后的服务信息：\n{project.to_dict()}')
    return project


def update_module(project, yapi_module):
    """ yapi 的模块更新到测试平台的模块 """

    with db.auto_commit():
        # 存模块原始信息
        original_yapi_module = YapiModule.get_first(yapi_id=yapi_module["_id"]) or YapiModule()
        original_yapi_module.yapi_project = yapi_module["project_id"]
        original_yapi_module.yapi_name = yapi_module["name"]
        original_yapi_module.yapi_id = yapi_module["_id"]
        original_yapi_module.yapi_data = json.dumps(yapi_module, ensure_ascii=False, indent=4)
        if not original_yapi_module.id:
            db.session.add(original_yapi_module)
        app.logger.info(f'原始yapi模块信息: \n{yapi_module}')

        # 存解析后的模块数据
        module = ApiModule.get_first(yapi_id=yapi_module["_id"]) or ApiModule()
        module.project_id = project.id
        module.name = yapi_module["name"]
        module.yapi_id = yapi_module["_id"]
        if not module.id:
            module.num = module.get_insert_num(project_id=project.id)
            db.session.add(module)
    app.logger.info(f'解析yapi后的模块信息：\n{module.to_dict()}')
    return module


def update_api(project, module_and_api):
    """ 更新接口 """
    module_id = ""
    with db.auto_commit():
        for api_index, yapi_api in enumerate(module_and_api.get("list", [])):
            if assert_coding_format(yapi_api["title"]):
                app.logger.info(f'原始yapi接口信息: \n{yapi_api}')
                # 存原始信息
                original_yapi_api = YapiApiMsg.get_first(yapi_id=yapi_api["_id"]) or YapiApiMsg()
                original_yapi_api.yapi_project = yapi_api["project_id"]
                original_yapi_api.yapi_module = yapi_api["catid"]
                original_yapi_api.yapi_name = yapi_api["title"]
                original_yapi_api.yapi_id = yapi_api["_id"]
                original_yapi_api.yapi_data = json.dumps(yapi_api, ensure_ascii=False, indent=4)
                if not original_yapi_api.id:
                    db.session.add(original_yapi_api)

                # 更新接口信息
                module_id = module_id or ApiModule.get_first(yapi_id=yapi_api["catid"]).id
                api_msg = ApiMsg.get_first(yapi_id=yapi_api["_id"]) or ApiMsg()

                parse_path(api_msg, yapi_api)  # 处理接口地址
                parse_header(api_msg, yapi_api)  # 处理头部信息
                parse_query(api_msg, yapi_api)  # 处理查询字符串参数
                parse_data_type(api_msg, yapi_api)  # 处理请求数据类型
                parse_json(api_msg, yapi_api)  # 处理json参数
                parse_form(api_msg, yapi_api)  # 处理form参数

                api_msg.name = yapi_api["title"]
                api_msg.method = yapi_api["method"].upper()
                api_msg.yapi_id = yapi_api["_id"]
                api_msg.module_id = module_id
                api_msg.project_id = project.id
                if not api_msg.id:
                    api_msg.num = api_msg.get_insert_num(module_id=module_id)
                    db.session.add(api_msg)


def get_yapi_header(host, account, password):
    """ 登录yapi，获取set-cookie """
    try:
        login_res = requests.post(
            f'{host}/api/user/login',
            json={"email": account, "password": password}
        ).headers["Set-Cookie"]
        return {
            "Cookie": "_yapi_token=" + re.findall("_yapi_token=(.+?); ", login_res)[0] + "; " +
                      "_yapi_uid=" + re.findall("_yapi_uid=(.+?); ", login_res)[0],
        }
    except Exception as error:
        raise Exception("yapi登录失败，请检查配置的地址、账号、密码是否正确")


def get_group_list(host, headers, ignore_group):
    """ 获取分组列表
    yapi接口响应关键数据
    {
        "data": [
            {
                "_id": 119
            }
        ]
    }
    """
    group_list = requests.get(f'{host}/api/group/list', headers=headers).json()["data"]
    app.logger.info(f'获取到的分组列表：\n{group_list}')
    return pop_ignore(group_list, ignore_group, "group_name")


def get_group(host, group_id, headers):
    """ 根据 yapi 的分组id，获取分组信息 """
    group = requests.get(f'{host}/api/group/get?id={group_id}', headers=headers).json()["data"]
    app.logger.info(f'根据分组id {group_id} 获取到的分组：\n{group}')
    return {"id": group["_id"], "name": group["group_name"]}


def get_yapi_project_list(host, group_id, headers, ignore_project):
    """ 获取指定分组下的服务列表
    yapi接口响应
    {
        "data": {
            "list": [
                {
                    "_id": 74,
                    "name": "XXX服务",
                    "group_id": 41
                }
            ]
        }
    }
    """
    project_list = requests.get(
        f'{host}/api/project/list?group_id={group_id}&page=1&limit=1000',
        headers=headers,
    ).json()["data"]["list"]
    app.logger.info(f'根据分组 {group_id} 获取到的服务：\n{project_list}')
    return pop_ignore(project_list, ignore_project, "name")


def get_module_list(host, project_id, headers):
    """ 获取模块id
    yapi 接口响应
    {
        "_id": 74,
        "name": "OCR重构",
        "cat": [
            {
                "_id": 419,
                "name": "公共分类",
                "project_id": 74,
            }
        ],
    }
    """
    res = requests.get(
        f'{host}/api/project/get?id={project_id}', headers=headers
    ).json()
    app.logger.info(f'根据服务id {project_id} 获取到的分类：\n{res.get("data", {}).get("cat", [])}')
    return res.get("data", {}).get("cat", [])


def get_module_and_api(host, project_id, headers):
    """ 导出服务下的模块和接口
    yapi 接口返回
    [
      {
        "list": [
          {
            "_id": 2406,
            "method": "POST",
            "catid": 427,  # yapi的模块id
            "title": "识别二维码/条形码",
            "path": "/api/v1/ocr/codeOcr/findBarCodeResult",
            "project_id": 74,
            "req_query": [
              {
                "name": "fileId",
                "example": "850970",
                "desc": ""
              }
            ],
            "req_headers": [
              {
                "name": "Content-Type",
                "value": "application/x-www-form-urlencoded"
              }
            ],
            "desc": "",
            "req_body_type": "form",
            "req_body_form": [],
            "req_body_other": ""
          }
        ]
      }
    ]
    """
    data = requests.get(
        f"{host}/api/plugin/export?type=json&pid={project_id}&status=all&isWiki=false",
        headers=headers
    ).json()
    app.logger.info(f"根据服务id {project_id} 获取到的数据：\n{data}")
    return data


def get_yapi_config(is_disable_ignore):
    """ 获取解析配置信息
    is_disable_ignore: 是否禁用过滤条件
    """
    # 获取yapi平台的配置信息
    conf_list = Config.query.filter(Config.name.in_([
        "yapi_host", "yapi_account", "yapi_password", "ignore_keyword_for_group", "ignore_keyword_for_project"
    ])).all()
    conf = {conf.name: conf.value for conf in conf_list}
    # 如果指定了不使用过滤条件，则把ignore_keyword_for_group、ignore_keyword_for_project 置为空列表
    conf["ignore_group"] = [] if is_disable_ignore else json.loads(conf.get("ignore_keyword_for_group", "[]"))
    conf["ignore_project"] = [] if is_disable_ignore else json.loads(conf.get("ignore_keyword_for_project", "[]"))
    return conf


def get_is_update_project_list(yapi_host, headers, project_id, group, ignore_project):
    """ 获取要更新的服务列表 """
    project_list = []

    # 传了指定的服务id，则只获取对应服务在yapi的服务信息
    if project_id:
        yapi_id = ApiProject.get_first(id=project_id).yapi_id
        for project in get_yapi_project_list(yapi_host, group["_id"], headers, ignore_project):
            if project["_id"] == yapi_id:
                project_list = [project]
                break
    else:  # 没有指定服务id，则获取分组下的所有服务
        project_list = get_yapi_project_list(yapi_host, group["_id"], headers, ignore_project)

    return project_list


class YapiPullAll(LoginRequiredView):

    def post(self):
        """ 拉取yapi的所有数据
        id: 指定服务在测试平台的id
        is_disable_ignore: 是否禁用配置的过滤条件
        """
        # 请求参数
        request_project_id, is_disable_ignore = request.json.get("id"), request.json.get("is_disable_ignore")

        # 获取yapi平台的配置信息
        conf = get_yapi_config(is_disable_ignore)

        # 获取头部信息
        headers = get_yapi_header(conf.get("yapi_host"), conf.get("yapi_account"), conf.get("yapi_password"))

        # 遍历要更新的分组列表
        for group in get_group_list(conf.get("yapi_host"), headers, conf.get("ignore_group")):

            # 获取当前分组下要更新的服务列表
            project_list = get_is_update_project_list(
                conf.get("yapi_host"), headers, request_project_id, group, conf.get("ignore_project")
            )

            # 遍历当前分组下要更新的服务列表
            for yapi_project in project_list:

                # 更新服务
                app.logger.info(f"服务：{yapi_project}")
                if assert_coding_format(yapi_project.get("name")):

                    # 更新服务
                    api_test_project = update_project(yapi_project)

                    # 更新模块
                    for yapi_module in get_module_list(conf.get("yapi_host"), yapi_project["_id"], headers):
                        app.logger.info(f"模块：{yapi_module}")
                        if assert_coding_format(yapi_module["name"]):
                            update_module(api_test_project, yapi_module)

                    # 更新接口信息
                    for module_and_api in get_module_and_api(conf.get("yapi_host"), yapi_project["_id"], headers):
                        update_api(api_test_project, module_and_api)

        return app.restful.success("数据更新完成")


class YapiPullProject(LoginRequiredView):

    def post(self):
        """ 拉取yapi的服务数据，同步到测试平台
        id: 指定服务在测试平台的id
        is_disable_ignore: 是否禁用配置的过滤条件
        """
        # 请求参数
        request_project_id, is_disable_ignore = request.json.get("id"), request.json.get("is_disable_ignore")

        # 获取yapi平台的配置信息
        conf = get_yapi_config(is_disable_ignore)

        # 获取头部信息
        headers = get_yapi_header(conf.get("yapi_host"), conf.get("yapi_account"), conf.get("yapi_password"))

        # 遍历要更新的分组列表
        for group in get_group_list(conf.get("yapi_host"), headers, conf.get("ignore_group")):

            # 获取当前分组下要更新的服务列表
            project_list = get_is_update_project_list(
                conf.get("yapi_host"), headers, request_project_id, group, conf.get("ignore_project")
            )

            # 遍历当前分组下要更新的服务列表
            for yapi_project in project_list:

                # 更新服务
                app.logger.info(f"服务：{yapi_project}")
                if assert_coding_format(yapi_project.get("name")):
                    update_project(yapi_project)

        return app.restful.success("数据更新完成")


class DiffByYapi(LoginRequiredView):

    def post(self):
        """ 接口对比，用于监控swagger接口是否有改动
        is_disable_ignore：是否使用配置的忽略项
        group_name：指定分组，若没有指定，则取全部分组
        """

        # 获取yapi平台的配置信息
        conf = get_yapi_config(is_disable_ignore=request.json.get("is_disable_ignore"))

        # 获取头部信息
        headers = get_yapi_header(conf.get("yapi_host"), conf.get("yapi_account"), conf.get("yapi_password"))

        # 获取分组信息
        group_list = get_group_list(conf.get("yapi_host"), headers, [])  # 所有分组列表
        if request.json and request.json.get("group_name"):
            group_list = [group for group in group_list if group["group_name"] == request.json.get("group_name")]

        # 对比总结果
        diff_is_changed = False
        title = request.json.get("group_name") or "全部分组"
        # 对比结果统计信息
        diff_summary = {
            "title": title,
            "project": {"totle": 0, "add": 0, "modify": 0, "remove": 0, "errorCode": 0},  # 新增、修改、删除、编码异常
            "module": {"totle": 0, "add": 0, "modify": 0, "remove": 0, "errorCode": 0},
            "api": {"totle": 0, "add": 0, "modify": 0, "remove": 0, "errorCode": 0}
        }
        # 对比详细记录，做root节点的children
        diff_detail = {"nodeData": {"topic": title, "root": True, "children": []}}

        # 遍历分组，取服务信息
        for yapi_group in group_list:
            group_str = f'分组【{yapi_group["group_name"]}】'

            # 获取当分组在数据库中存的服务信息，和获取和到的服务对比
            group_detail = {"topic": yapi_group["group_name"], "children": []}
            project_detail_add = {"topic": "新增服务", "children": []}
            project_detail_change = {"topic": "已修改服务", "children": []}
            project_detail_remove = {"topic": "已删除服务", "children": []}
            db_project_list = {project.yapi_id: project for project in
                               YapiProject.get_all(yapi_group=yapi_group["_id"])}
            for yapi_project in get_yapi_project_list(conf.get("yapi_host"), yapi_group["_id"], headers, []):
                diff_summary["project"]["totle"] += 1

                # 对比服务
                if assert_coding_format(yapi_project["name"]):
                    project = db_project_list.pop(yapi_project["_id"], None)
                    if project:
                        project_data = json.loads(project.yapi_data)
                        project_detail_change_detail = {"topic": f'{project_data.get("name")}', "children": []}
                        # 对比服务名
                        if project_data.get("name") != yapi_project["name"]:
                            diff_is_changed = True
                            diff_summary["project"]["modify"] += 1
                            project_detail_change_detail["children"].append(
                                {"topic": f'服务名变更为【{yapi_project["name"]}】'})
                            if project_detail_change_detail["children"]:
                                project_detail_change["children"].append(project_detail_change_detail)
                    else:
                        diff_is_changed = True
                        diff_summary["project"]["add"] += 1
                        project_detail_add["children"].append(
                            {"topic": f'{group_str}下，新增服务【{yapi_project["name"]}】'})
                else:
                    diff_summary["project"]["errorCode"] += 1
                    continue

                # 获取当服务在数据库中存的模块信息，和获取和到的模块对比
                project_detail = {"topic": yapi_project["name"], "children": []}
                module_detail_add = {"topic": "新增模块", "children": []}
                module_detail_change = {"topic": "已修改模块", "children": []}
                module_detail_remove = {"topic": "已删除模块", "children": []}
                db_module_list = {module.yapi_id: module for module in
                                  YapiModule.get_all(yapi_project=yapi_project["_id"])}
                for yapi_module in get_module_list(conf.get("yapi_host"), yapi_project["_id"], headers):
                    diff_summary["module"]["totle"] += 1
                    if assert_coding_format(yapi_module["name"]):
                        db_module = db_module_list.pop(yapi_module["_id"], None)
                        if db_module:
                            module_data = json.loads(db_module.yapi_data)
                            module_detail_change_detail = {"topic": f'{module_data.get("name")}', "children": []}
                            if module_data.get("name") != yapi_module["name"]:
                                diff_is_changed = True
                                diff_summary["module"]["modify"] += 1
                                module_detail_change_detail["children"].append(
                                    {"topic": f'名称变更为【{yapi_module["name"]}】'})
                                if module_detail_change_detail["children"]:
                                    module_detail_change["children"].append(module_detail_change_detail)
                        else:
                            diff_is_changed = True
                            diff_summary["module"]["add"] += 1
                            module_detail_add["children"].append({"topic": f'新增模块:【{yapi_module["name"]}】'})
                    else:
                        diff_summary["module"]["errorCode"] += 1
                        continue
                else:
                    # 对比完后，数据库数据中还有模块，则说明该模块在yapi已删除
                    if db_module_list:
                        diff_is_changed = True
                        for module_id, module in db_module_list.items():
                            diff_summary["module"]["remove"] += 1
                            module_detail_remove["children"].append({
                                "topic": f'模块【{json.loads(module.yapi_data).get("name")}】已删除'
                            })
                # 模块对比完后，记录模块对比结果
                if module_detail_add["children"]:
                    project_detail["children"].append(module_detail_add)
                if module_detail_change["children"]:
                    project_detail["children"].append(module_detail_change)
                if module_detail_remove["children"]:
                    project_detail["children"].append(module_detail_remove)

                # 获取当服务在数据库中存的接口信息，和获取和到的接口对比
                for module_and_api in get_module_and_api(conf.get("yapi_host"), yapi_project["_id"], headers):
                    module_detail = {"topic": module_and_api["name"], "children": []}
                    api_detail_add = {"topic": "新增接口", "children": []}
                    api_detail_change = {"topic": "已修改接口", "children": []}
                    api_detail_remove = {"topic": "已删除接口", "children": []}
                    db_api_list = {}
                    db_module = YapiModule.get_first(yapi_project=yapi_project["_id"], yapi_name=module_and_api["name"])
                    if db_module:
                        db_api_list = {y_api.yapi_id: y_api for y_api in
                                       YapiApiMsg.get_all(yapi_module=db_module.yapi_id)}
                    for yapi_api in module_and_api["list"]:
                        diff_summary["api"]["totle"] += 1
                        api_is_changed = False
                        if assert_coding_format(yapi_api.get("title")):
                            db_api = db_api_list.pop(yapi_api.get("_id"), None)
                            if db_api:
                                db_data = json.loads(db_api.yapi_data)
                                api_detail_change_detail = {"topic": f'{db_data.get("title")}', "children": []}
                                # 接口名
                                if db_data.get("title") != yapi_api.get("title"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'名称变更为【{yapi_api.get("title")}】'
                                    })
                                # 请求方法
                                if db_data.get("method") != yapi_api.get("method"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'请求方法由【{db_data.get("method")}】变更为【{yapi_api.get("method")}】'
                                    })
                                # 地址
                                if db_data.get("path") != yapi_api.get("path"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'接口地址由【{db_data.get("path")}】变更为【{yapi_api.get("path")}】'
                                    })
                                # 头部信息增加
                                if not json.dumps(db_data.get("req_headers")) and json.dumps(
                                        yapi_api.get("req_headers")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'头部信息由【{db_data.get("req_headers")}】变更为【{yapi_api.get("req_headers")}】'
                                    })
                                # 头部信息删除
                                elif json.dumps(db_data.get("req_headers")) and not json.dumps(
                                        yapi_api.get("req_headers")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'头部信息由【{db_data.get("req_headers")}】变更为【{yapi_api.get("req_headers")}】'
                                    })
                                else:
                                    # 头部信息修改
                                    for args in db_data.get("req_headers"):
                                        args.pop("_id", None)
                                    for args in yapi_api.get("req_headers"):
                                        args.pop("_id", None)
                                    if json.dumps(db_data.get("req_headers"), sort_keys=True) != json.dumps(
                                            yapi_api.get("req_headers"), sort_keys=True):
                                        diff_is_changed = True
                                        api_is_changed = True
                                        api_detail_change_detail["children"].append({
                                            "topic": f'头部信息由【{db_data.get("req_headers")}】变更为【{yapi_api.get("req_headers")}】'
                                        })

                                # 查询字符串参数增加
                                if not json.dumps(db_data.get("req_query")) and json.dumps(yapi_api.get("req_query")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'查询字符串参数由【{db_data.get("req_query")}】变更为【{yapi_api.get("req_query")}】'
                                    })
                                # 查询字符串参数删除
                                elif json.dumps(db_data.get("req_query")) and not json.dumps(yapi_api.get("req_query")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'查询字符串参数由【{db_data.get("req_query")}】变更为【{yapi_api.get("req_query")}】'
                                    })
                                else:
                                    # 头查询字符串参数修改
                                    for args in db_data.get("req_query"):
                                        args.pop("_id", None)
                                    for args in yapi_api.get("req_query"):
                                        args.pop("_id", None)
                                    if json.dumps(db_data.get("req_query"), sort_keys=True) != json.dumps(
                                            yapi_api.get("req_query"), sort_keys=True):
                                        diff_is_changed = True
                                        api_is_changed = True
                                        api_detail_change_detail["children"].append({
                                            "topic": f'查询字符串参数由【{db_data.get("req_query")}】变更为【{yapi_api.get("req_query")}】'
                                        })

                                # 请求参数类型
                                if db_data.get("req_body_type") != yapi_api.get("req_body_type"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'请求参数类型由【{db_data.get("req_body_type")}】变更为【{yapi_api.get("req_body_type")}】'
                                    })
                                # 请求json参数
                                if db_data.get("req_body_other") != yapi_api.get("req_body_other"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'json参数由【{db_data.get("req_body_other")}】变更为【{yapi_api.get("req_body_other")}】'
                                    })
                                # form参数增加
                                if not json.dumps(db_data.get("req_body_form")) and json.dumps(
                                        yapi_api.get("req_body_form")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'form参数由【{db_data.get("req_body_form")}】变更为【{yapi_api.get("req_body_form")}】'
                                    })
                                # form参数删除
                                elif json.dumps(db_data.get("req_body_form")) and not json.dumps(
                                        yapi_api.get("req_body_form")):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'form参数由【{db_data.get("req_body_form")}】变更为【{yapi_api.get("req_body_form")}】'
                                    })
                                else:
                                    # form参数修改
                                    for args in db_data.get("req_body_form"):
                                        args.pop("_id", None)
                                    for args in yapi_api.get("req_body_form"):
                                        args.pop("_id", None)
                                    if json.dumps(db_data.get("req_body_form"), sort_keys=True) != json.dumps(
                                            yapi_api.get("req_body_form"), sort_keys=True):
                                        diff_is_changed = True
                                        api_is_changed = True
                                        api_detail_change_detail["children"].append({
                                            "topic": f'form参数由【{db_data.get("req_body_form")}】变更为【{yapi_api.get("req_body_form")}】'
                                        })

                                # 响应数据类型
                                if db_data.get("res_body_type") != yapi_api.get("res_body_type"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'响应数据类型由【{db_data.get("res_body_type")}】变更为【{yapi_api.get("res_body_type")}】'
                                    })
                                # 响应参数
                                if db_data.get("res_body") != yapi_api.get("res_body"):
                                    diff_is_changed = True
                                    api_is_changed = True
                                    api_detail_change_detail["children"].append({
                                        "topic": f'响应体由【{db_data.get("res_body")}】变更为【{yapi_api.get("res_body")}】'
                                    })
                                diff_summary["api"]["modify"] += api_is_changed
                                if api_detail_change_detail["children"]:
                                    api_detail_change["children"].append(api_detail_change_detail)
                            else:
                                diff_summary["api"]["add"] += 1
                                api_detail_add["children"].append({"topic": f'新增接口:【{yapi_api.get("title")}】'})
                        else:
                            diff_summary["api"]["errorCode"] += 1
                            continue
                    else:
                        # 对比完后，数据库数据中还有接口，则说明该接口在yapi已删除
                        if db_api_list:
                            diff_is_changed = True
                            for api_id, db_api in db_api_list.items():
                                diff_summary["api"]["remove"] += 1
                                api_detail_remove["children"].append({"topic": f"接口【{db_api.yapi_name}】已删除"})
                    # 添加接口的变化，有变化才添加
                    if api_detail_add["children"]:
                        module_detail["children"].append(api_detail_add)
                    if api_detail_change["children"]:
                        module_detail["children"].append(api_detail_change)
                    if api_detail_remove["children"]:
                        module_detail["children"].append(api_detail_remove)
                    if module_detail["children"]:  # 把模块下的接口变化添加到服务中
                        project_detail["children"].append(module_detail)
                # 把服务下游的变化添加到分组中
                if project_detail["children"]:
                    group_detail["children"].append(project_detail)
            else:
                # 对比完后，数据库数据中还有服务，则说明该服务在yapi已删除
                if db_project_list:
                    diff_is_changed = True
                    for project_id, project in db_project_list.items():
                        diff_summary["project"]["remove"] += 1
                        project_detail_remove["children"].append({
                            "topic": f'{group_str}下，服务【{json.loads(project.yapi_data).get("name")}】已删除'
                        })
            # 添加服务变化，有才添加，没有就不添加
            if project_detail_add["children"]:
                group_detail["children"].append(project_detail_add)
            if project_detail_change["children"]:
                group_detail["children"].append(project_detail_change)
            if project_detail_remove["children"]:
                group_detail["children"].append(project_detail_remove)
            if group_detail["children"]:
                diff_detail["nodeData"]["children"].append(group_detail)

        # 存对比结果
        with db.auto_commit():
            yapi_diff_record = YapiDiffRecord()
            yapi_diff_record.name = title
            yapi_diff_record.is_changed = diff_is_changed
            yapi_diff_record.diff_summary = json.dumps(diff_summary, ensure_ascii=False, indent=4)
            yapi_diff_record.create_user = g.user_id
            db.session.add(yapi_diff_record)
        FileUtil.save_diff_result(yapi_diff_record.id, diff_detail)

        # 有改动则发送报告
        if diff_is_changed:
            send_diff_api_message(
                content=diff_summary,
                report_id=yapi_diff_record.id,
                addr=request.json.get("addr") or Config.get_default_diff_message_send_addr()
            )
        return app.restful.success("对比完成", data=yapi_diff_record.to_dict())


class DiffByFront(LoginRequiredView):

    def post(self):
        """ 接口对比，用于监控前端使用的接口与swagger是否一致 """
        return app.restful.success("对比完成")


class ExportDiffRecordAsXmind(LoginRequiredView):

    def get(self):
        """ 导出为xmind """
        diff_data = FileUtil.get_diff_result(request.args.get("id"))
        file_name = f'{diff_data.get("nodeData", {}).get("topic", {})}.xmind'
        file_path = os.path.join(DIFF_RESULT, file_name)
        FileUtil.delete_file(file_path)
        make_xmind(file_path, diff_data)
        return send_from_directory(DIFF_RESULT, file_name, as_attachment=True)


class GetDiffRecordList(LoginRequiredView):

    def get(self):
        """ 接口对比结果列表 """
        return app.restful.success("获取成功", data=YapiDiffRecord.make_pagination({
            "pageNum": request.args.get("pageNum"),
            "pageSize": request.args.get("pageSize"),
            "create_user": request.args.get("create_user"),
            "name": request.args.get("name")
        }))


class GetDiffRecordProject(LoginRequiredView):

    def get(self):
        """ 获取有对比结果的服务列表 """
        project_list = YapiDiffRecord.query.with_entities(YapiDiffRecord.name).distinct().all()
        return app.restful.success("获取成功",
                                   data=[{"key": project[0], "value": project[0]} for project in project_list])


class GetShowDiffRecord(LoginRequiredView):

    def get(self):
        """ 展示对比结果详情 """
        return app.restful.success("获取成功", data=FileUtil.get_diff_result(request.args.get("id")))


assist.add_url_rule("/yapi/pull/all", view_func=YapiPullAll.as_view("YapiPullAll"))
assist.add_url_rule("/yapi/diff/byApi", view_func=DiffByYapi.as_view("DiffByYapi"))
assist.add_url_rule("/yapi/diff/byFront", view_func=DiffByFront.as_view("DiffByFront"))
assist.add_url_rule("/yapi/pull/project", view_func=YapiPullProject.as_view("YapiPullProject"))
assist.add_url_rule("/yapi/record/list", view_func=GetDiffRecordList.as_view("GetDiffRecordList"))
assist.add_url_rule("/yapi/record/show", view_func=GetShowDiffRecord.as_view("GetShowDiffRecord"))
assist.add_url_rule("/yapi/record/project", view_func=GetDiffRecordProject.as_view("GetDiffRecordProject"))
assist.add_url_rule("/yapi/diff/download", view_func=ExportDiffRecordAsXmind.as_view("ExportDiffRecordAsXmind"))
