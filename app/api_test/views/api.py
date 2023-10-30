# -*- coding: utf-8 -*-
import copy
from threading import Thread

from flask import current_app as app, request, send_from_directory, g

from app.baseModel import db
from app.api_test.blueprint import api_test
from utils.util.fileUtil import STATIC_ADDRESS
from utils.parse.parseExcel import parse_file_content
from utils.client.runApiTest import RunApi
from app.api_test.models.module import ApiModule as Module
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.report import ApiReport as Report
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.suite import ApiCaseSuite as CaseSuite
from app.api_test.models.step import ApiStep as Step
from app.config.models.config import Config
from app.api_test.forms.api import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiByIdForm, \
    ApiFromForm, ChangeLevel, ChangeStatus
from config import assert_mapping_list


@api_test.get("/apiMsg/assertMapping")
def api_get_assert_mapping():
    """ 获取断言类型 """
    return app.restful.success("获取成功", data=assert_mapping_list)


@api_test.login_get("/apiMsg/methods")
def api_get_methods_mapping():
    """ 获取配置的请求方法列表 """
    return app.restful.success(
        "获取成功",
        data=[{"value": method} for method in Config.get_http_methods().split(",")]
    )


@api_test.login_get("/apiMsg/list")
def api_get_api_list():
    """ 根据模块查接口list """
    form = ApiListForm().do_validate()
    return app.restful.success(data=Api.make_pagination(form))


@api_test.login_post("/apiMsg/level")
def api_get_change_api_level():
    """ 修改接口重要级别 """
    form = ChangeLevel().do_validate()
    form.api.update(form.data)
    return app.restful.success("修改成功")


@api_test.login_post("/apiMsg/status")
def api_get_change_api_status():
    """ 修改接口是否被废弃 """
    form = ChangeStatus().do_validate()
    form.api.update(form.data)
    return app.restful.success("修改成功")


@api_test.login_get("/apiMsg/from")
def api_get_api_from():
    """ 根据接口地址获取接口的归属信息 """
    form = ApiFromForm().do_validate()
    api_list = []
    for api in form.api_list:  # 多个服务存在同一个接口地址的情况
        project = Project.get_first(id=api.project_id)
        module_name = Module.get_from_path(api.module_id)
        api_dict = api.to_dict()
        api_dict["from"] = f'【{project.name}_{module_name}_{api.name}】'
        api_list.append(api_dict)
    return app.restful.success(msg='获取成功', data=api_list)


@api_test.login_get("/apiMsg/toStep")
def api_get_api_to_step():
    """ 查询哪些用例下的步骤引用了当前接口 """
    form = ApiFromForm().do_validate()
    case_list, case_dict, project_dict = [], {}, {}  # 可能存在重复获取数据的请，获取到就存下来，一条数据只查一次库
    for api in form.api_list:  # 多个服务存在同一个接口地址的情况
        steps = Step.get_all(api_id=api.id)  # 存在一个接口在多个步骤调用的情况
        for step in steps:
            # 获取步骤所在的用例
            if step.case_id not in case_dict:
                case_dict[step.case_id] = Case.get_first(id=step.case_id)
            case = case_dict[step.case_id]

            # 获取用例所在的用例集
            suite = CaseSuite.get_first(id=case.suite_id)
            suite_from_path = CaseSuite.get_from_path(suite.id)

            # 获取用例集所在的服务
            if suite.project_id not in project_dict:
                project_dict[suite.project_id] = Project.get_first(id=suite.project_id)
            project = project_dict[suite.project_id]

            case_dict = case.to_dict()
            case_dict["from"] = f'【{project.name if project else None}_{suite_from_path}_{case.name}_{step.name}】'
            case_list.append(copy.deepcopy(case_dict))

    return app.restful.success(msg='获取成功', data=case_list)


@api_test.post("/apiMsg/upload")
def api_upload_api():
    """ 从excel中导入接口 """
    file, module, user_id = request.files.get("file"), Module.get_first(id=request.form.get("id")), g.user_id
    if not module:
        return app.restful.fail("模块不存在")
    if file and file.filename.endswith("xls"):
        excel_data = parse_file_content(file.read())  # [{"请求类型": "get", "接口名称": "xx接口", "addr": "/api/v1/xxx"}]
        with db.auto_commit():
            for api_data in excel_data:
                new_api = Api()
                for key, value in api_data.items():
                    if hasattr(new_api, key):
                        setattr(new_api, key, value)
                new_api.method = api_data.get("method", "post").upper()
                new_api.num = new_api.get_insert_num(module_id=module.id)
                new_api.project_id = module.project_id
                new_api.module_id = module.id
                new_api.create_user = user_id
                db.session.add(new_api)
        return app.restful.success("接口导入成功")
    return app.restful.fail("请上传后缀为xls的Excel文件")


@api_test.login_get("/apiMsg/template/download")
def api_get_api_template():
    """ 下载接口导入模板 """
    return send_from_directory(STATIC_ADDRESS, "接口导入模板.xls", as_attachment=True)


@api_test.login_put("/apiMsg/sort")
def api_change_api_sort():
    """ 修改接口的排序 """
    Api.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@api_test.login_get("/apiMsg")
def api_get_api():
    """ 获取接口 """
    form = GetApiByIdForm().do_validate()
    return app.restful.success(data=form.api.to_dict())


@api_test.login_post("/apiMsg")
def api_add_api():
    """ 新增接口 """
    form = AddApiForm().do_validate()
    form.num.data = Api.get_insert_num(module_id=form.module_id.data)
    new_api = Api().create(form.data)
    return app.restful.success(f'接口【{form.name.data}】新建成功', data=new_api.to_dict())


@api_test.login_put("/apiMsg")
def api_change_api():
    """ 修改接口 """
    form = EditApiForm().do_validate()
    form.api.update(form.data)
    return app.restful.success(f'接口【{form.name.data}】修改成功', form.api.to_dict())


@api_test.login_delete("/apiMsg")
def api_delete_api():
    """ 删除接口 """
    form = DeleteApiForm().do_validate()
    form.api.delete()
    return app.restful.success(f'接口【{form.api.name}】删除成功')


@api_test.login_post("/apiMsg/run")
def api_run_api():
    """ 运行接口 """
    form = RunApiMsgForm().do_validate()
    api, api_list = form.api_list[0], form.api_list
    batch_id = Report.get_batch_id()
    for env_code in form.env_list.data:
        report = Report.get_new_report(
            batch_id=batch_id,
            run_id=api.id,
            trigger_id=form.apis.data,
            name=api.name,
            run_type="api",
            env=env_code,
            create_user=g.user_id,
            project_id=form.projectId.data
        )

        # 新起线程运行接口
        Thread(
            target=RunApi(
                project_id=form.projectId.data,
                run_name=report.name,
                api_ids=api_list,
                report_id=report.id,
                env_code=env_code
            ).parse_and_run
        ).start()
    return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"batch_id": batch_id})
