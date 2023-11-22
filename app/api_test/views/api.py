# -*- coding: utf-8 -*-
from threading import Thread

from flask import current_app as app, request, send_from_directory, g

from ..blueprint import api_test
from ...base_form import ChangeSortForm
from ..model_factory import ApiModule as Module, ApiProject as Project, ApiReport as Report, ApiMsg as Api, \
    ApiCase as Case, ApiCaseSuite as CaseSuite, ApiStep as Step
from ..forms.api import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiForm, \
    GetApiFromForm, ChangeLevel, ChangeStatus
from utils.util.file_util import STATIC_ADDRESS
from utils.parse.parse_excel import parse_file_content
from utils.client.run_api_test import RunApi
from ...config.models.run_env import RunEnv


@api_test.login_get("/api/list")
def api_get_api_list():
    """ 根据模块查接口list """
    form = ApiListForm()
    if form.detail:
        get_filed = [Api.id, Api.name, Api.project_id, Api.module_id, Api.addr, Api.method, Api.use_count, Api.level,
                     Api.status]
    else:
        get_filed = Api.get_simple_filed_list()
    return app.restful.get_success(Api.make_pagination(form, get_filed=get_filed))


@api_test.login_put("/api/sort")
def api_change_api_sort():
    """ 修改接口的排序 """
    form = ChangeSortForm()
    Api.change_sort(**form.model_dump())
    return app.restful.change_success()


@api_test.login_post("/api/level")
def api_get_change_api_level():
    """ 修改接口重要级别 """
    form = ChangeLevel()
    form.api.model_update(form.model_dump())
    return app.restful.change_success()


@api_test.login_post("/api/status")
def api_get_change_api_status():
    """ 修改接口状态 """
    form = ChangeStatus()
    Api.query.filter(Api.id == form.id).update({"status": form.status.value})
    return app.restful.change_success()


@api_test.login_get("/api/from")
def api_get_api_from():
    """ 根据接口地址获取接口的归属信息 """
    form = GetApiFromForm()
    api_list = []
    for api_id in form.api_id_list:  # 多个服务存在同一个接口地址的情况
        api = Api.get_first(id=api_id)
        project_info = Project.db.session.query(Project.name).filter(Project.id == api.project_id).first()
        project_name = project_info[0] if project_info else None
        module_name = Module.get_from_path(api.module_id)
        api_dict = api.to_dict()
        api_dict["from"] = f'【{project_name}_{module_name}_{api.name}】'
        api_list.append(api_dict)
    return app.restful.get_success(api_list)


@api_test.login_get("/api/to-step")
def api_get_api_to_step():
    """ 查询哪些用例下的步骤引用了当前接口 """
    form = GetApiFromForm()
    case_list, case_dict, project_dict = [], {}, {}  # 可能存在重复获取数据的请，获取到就存下来，一条数据只查一次库
    for api_id in form.api_id_list:  # 多个服务存在同一个接口地址的情况
        # 存在一个接口在多个步骤调用的情况
        step_info = Step.db.session.query(Step.name, Step.case_id).filter_by(api_id=api_id).all()
        for step in step_info:
            step_name, case_id = step[0], step[1]
            # 获取步骤所在的用例
            if case_id not in case_dict:
                case_info = Case.db.session.query(
                    Case.name, Case.status, CaseSuite.id, CaseSuite.project_id
                ).filter(Case.id == case_id, Case.suite_id == CaseSuite.id).first()
                case_dict[case_id] = {
                    "id": case_id,
                    "name": case_info[0],
                    "status": case_info[1],
                    "suite_id": case_info[2],
                    "project_id": case_info[3]
                }
            case = case_dict[case_id]
            suite_id, project_id = case["suite_id"], case["project_id"]

            # 获取用例所在的用例集
            suite_from_path = CaseSuite.get_from_path(suite_id)

            # 获取用例集所在的服务
            if project_id not in project_dict:
                project_info = Project.db.session.query(Project.name).filter(Project.id == project_id).first()
                project_dict[project_id] = {"name": project_info[0] if project_info else None}  # 可能服务已经删除了
            project = project_dict[project_id]
            case["from"] = f'【{project["name"]}_{suite_from_path}_{case["name"]}_{step_name}】'
            case_list.append(case)

    return app.restful.get_success(case_list)


@api_test.post("/api/upload")
def api_upload_api():
    """ 从excel中导入接口 """
    file, module, user_id = request.files.get("file"), Module.get_first(id=request.form.get("id")), g.user_id
    if not module:
        return app.restful.fail("模块不存在")
    if file and file.filename.endswith("xls"):
        excel_data = parse_file_content(file.read())  # [{"请求类型": "get", "接口名称": "xx接口", "addr": "/api/v1/xxx"}]
        with Api.db.auto_commit():
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
                Api.db.session.add(new_api)
        return app.restful.upload_success()
    return app.restful.fail("请上传后缀为xls的Excel文件")


@api_test.login_get("/api/template/download")
def api_get_api_template():
    """ 下载接口导入模板 """
    return send_from_directory(STATIC_ADDRESS, "接口导入模板.xls", as_attachment=True)


@api_test.login_get("/api")
def api_get_api():
    """ 获取接口 """
    form = GetApiForm()
    return app.restful.get_success(form.api.to_dict())


@api_test.login_post("/api")
def api_add_api():
    """ 新增接口 """
    form = AddApiForm()
    Api.model_create(form.model_dump())
    return app.restful.add_success()


@api_test.login_put("/api")
def api_change_api():
    """ 修改接口 """
    form = EditApiForm()
    form.api.model_update(form.model_dump())
    return app.restful.change_success()


@api_test.login_delete("/api")
def api_delete_api():
    """ 删除接口 """
    form = DeleteApiForm()
    Api.delete_by_id(form.id)
    return app.restful.delete_success()


@api_test.login_post("/api/run")
def api_run_api():
    """ 运行接口 """
    form = RunApiMsgForm()
    batch_id = Report.get_batch_id()
    summary = Report.get_summary_template()
    for env_code in form.env_list:
        env = RunEnv.get_data_by_id_or_code(env_code)
        summary["env"]["code"], summary["env"]["name"] = env.code, env.name
        report = Report.get_new_report(
            batch_id=batch_id,
            trigger_id=form.api_list,
            name=form.api_name,
            run_type="api",
            env=env_code,
            project_id=form.project_id,
            summary=summary
        )

        # 新起线程运行接口
        Thread(
            target=RunApi(
                api_id_list=form.run_api_id_list,
                report_id=report.id,
                env_code=env_code,
                env_name=env.name
            ).parse_and_run
        ).start()
    return app.restful.trigger_success({"batch_id": batch_id})
