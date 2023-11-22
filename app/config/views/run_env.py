# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import config_blueprint
from ...api_test.models.project import ApiProjectEnv, ApiProject
from ...app_test.models.project import AppUiProjectEnv, AppUiProject
from ...ui_test.models.project import WebUiProjectEnv, WebUiProject
from ...base_form import ChangeSortForm
from ..model_factory import BusinessLine, RunEnv
from ..forms.run_env import GetRunEnvForm, DeleteRunEnvForm, PostRunEnvForm, PutRunEnvForm, GetRunEnvListForm, \
    EnvToBusinessForm


@config_blueprint.get("/run-env/list")
def config_get_run_env_list():
    form = GetRunEnvListForm()
    if form.detail:
        get_filed = [RunEnv.id, RunEnv.name, RunEnv.code, RunEnv.desc, RunEnv.group]
    else:
        get_filed = [RunEnv.id, RunEnv.name, RunEnv.code, RunEnv.group]
    return app.restful.get_success(RunEnv.make_pagination(form, get_filed=get_filed))


@config_blueprint.get("/run-env/group")
def config_get_run_env_group():
    """ 环境分组列表 """
    group_list = RunEnv.query.with_entities(RunEnv.group).distinct().all()
    return app.restful.get_success([group[0] for group in group_list])


@config_blueprint.login_put("/run-env/sort")
def config_change_run_env_sort():
    """ 修改排序 """
    form = ChangeSortForm()
    RunEnv.change_sort(**form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_put("/run-env/business")
def config_change_run_env_to_business():
    """ 运行环境与业务线的绑定关系 """
    form = EnvToBusinessForm()
    RunEnv.env_to_business(form.env_list, form.business_list, form.command)
    return app.restful.change_success()


@config_blueprint.login_get("/run-env")
def config_get_run_env():
    """ 获取运行环境 """
    form = GetRunEnvForm()
    return app.restful.get_success(form.run_env.to_dict())


@config_blueprint.login_post("/run-env")
def config_add_run_env():
    """ 新增运行环境 """
    form = PostRunEnvForm()
    run_env = RunEnv.model_create_and_get(form.model_dump())

    # 给所有的服务/项目/app创建此运行环境的数据
    # ProjectEnvBusiness.add_env(run_env.id)
    ApiProjectEnv.add_env(run_env.id, ApiProject)
    WebUiProjectEnv.add_env(run_env.id, WebUiProject)
    AppUiProjectEnv.add_env(run_env.id, AppUiProject)

    # 把环境分配给设置了自动绑定的业务线
    business_list = BusinessLine.get_auto_bind_env_id_list()
    RunEnv.env_to_business([run_env.id], business_list, "add")

    return app.restful.add_success()


@config_blueprint.login_put("/run-env")
def config_change_run_env():
    """ 修改运行环境 """
    form = PutRunEnvForm()
    form.run_env.model_update(form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_delete("/run-env")
def config_delete_run_env():
    """ 删除运行环境 """
    form = DeleteRunEnvForm()
    form.run_env.delete()
    return app.restful.delete_success()
