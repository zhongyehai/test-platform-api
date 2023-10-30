# -*- coding: utf-8 -*-
from flask import current_app as app, request

from app.busines import ProjectEnvBusiness
from app.config.models.business import BusinessLine
from app.config.models.runEnv import RunEnv
from app.config.forms.runEnv import (
    GetRunEnvForm, DeleteRunEnvForm, PostRunEnvForm, PutRunEnvForm, GetRunEnvListForm, EnvToBusinessForm
)
from app.config.blueprint import config_blueprint


@config_blueprint.get("/runEnv/list")
def config_get_run_env_list():
    form = GetRunEnvListForm().do_validate()
    return app.restful.success(data=RunEnv.make_pagination(form))


@config_blueprint.get("/runEnv/group")
def config_get_run_env_group():
    """ 环境分组列表 """
    group_list = RunEnv.query.with_entities(RunEnv.group).distinct().all()
    return app.restful.success("获取成功", data=[group[0] for group in group_list])


@config_blueprint.login_put("/runEnv/sort")
def config_change_run_env_sort():
    """ 修改排序 """
    RunEnv.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@config_blueprint.login_put("/runEnv/toBusiness")
def config_change_run_env_to_business():
    """ 运行环境与业务线的绑定关系 """
    form = EnvToBusinessForm().do_validate()
    RunEnv.env_to_business(form.env_list.data, form.business_list.data, form.command.data)
    return app.restful.success("修改成功")


@config_blueprint.login_get("/runEnv")
def config_get_run_env():
    """ 获取运行环境 """
    form = GetRunEnvForm().do_validate()
    return app.restful.success("获取成功", data=form.run_env.to_dict())


@config_blueprint.login_post("/runEnv")
def config_add_run_env():
    """ 新增运行环境 """
    form = PostRunEnvForm().do_validate()
    form.num.data = RunEnv.get_insert_num()
    run_env = RunEnv().create(form.data)

    # 给所有的服务/项目/app创建此运行环境的数据
    ProjectEnvBusiness.add_env(run_env.id)

    # 把环境分配给设置了自动绑定的业务线
    business_list = BusinessLine.get_auto_bind_env_id_list()
    RunEnv.env_to_business([run_env.id], business_list, "add")

    return app.restful.success("新增成功", data=run_env.to_dict())


@config_blueprint.login_put("/runEnv")
def config_change_run_env():
    """ 修改运行环境 """
    form = PutRunEnvForm().do_validate()
    form.run_env.update(form.data)
    return app.restful.success("修改成功", data=form.run_env.to_dict())


@config_blueprint.login_delete("/runEnv")
def config_delete_run_env():
    """ 删除运行环境 """
    form = DeleteRunEnvForm().do_validate()
    form.run_env.delete()
    return app.restful.success("删除成功")
