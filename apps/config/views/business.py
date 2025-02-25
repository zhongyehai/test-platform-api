# -*- coding: utf-8 -*-
from flask import current_app as app, g

from ..blueprint import config_blueprint
from ..model_factory import BusinessLine
from ..forms.business import GetBusinessForm, DeleteBusinessForm, PostBusinessForm, PutBusinessForm, \
    GetBusinessListForm, BusinessToUserForm
from ...base_form import ChangeSortForm
from ...system.model_factory import User


@config_blueprint.login_get("/business/list")
def config_get_business_list():
    form = GetBusinessListForm()
    if form.detail:
        get_filed = [BusinessLine.id, BusinessLine.name, BusinessLine.code, BusinessLine.desc, BusinessLine.create_user]
    else:
        get_filed = BusinessLine.get_simple_filed_list()
    return app.restful.get_success(BusinessLine.make_pagination(form, get_filed=get_filed))


@config_blueprint.login_put("/business/sort")
def config_change_business_sort():
    """ 更新排序 """
    form = ChangeSortForm()
    BusinessLine.change_sort(**form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_put("/business/user")
def config_business_to_user():
    """ 批量管理业务线与用户的关系 绑定/解除绑定 """
    form = BusinessToUserForm()
    BusinessLine.business_to_user(form.business_list, form.user_list, form.command)
    return app.restful.change_success()


@config_blueprint.login_get("/business")
def config_get_business():
    """ 获取业务线 """
    form = GetBusinessForm()
    return app.restful.get_success(form.business.to_dict())


@config_blueprint.login_post("/business")
def config_add_business():
    """ 新增业务线 """
    form = PostBusinessForm()
    business = BusinessLine.model_create_and_get(form.model_dump())

    # 给创建者添加绑定关系，并生成新的token
    user = User.get_first(id=g.user_id)
    user.business_list.append(business.id)
    User.query.filter(User.id == user.id).update({"business_list": user.business_list})

    # 重新生成token
    token = user.make_access_token(g.api_permissions)
    return app.restful.add_success({"token": token, "business_id": user.business_list})


@config_blueprint.login_put("/business")
def config_change_business():
    """ 修改业务线 """
    form = PutBusinessForm()
    form.business.model_update(form.model_dump())
    return app.restful.change_success()


@config_blueprint.login_delete("/business")
def config_delete_business():
    """ 删除业务线 """
    form = DeleteBusinessForm()
    form.business.delete()
    return app.restful.delete_success()
