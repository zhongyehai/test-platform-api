# -*- coding: utf-8 -*-
from flask import current_app as app, g

from app.config.models.business import BusinessLine
from app.config.forms.business import (
    GetBusinessForm, DeleteBusinessForm, PostBusinessForm, PutBusinessForm, GetBusinessListForm, BusinessToUserForm
)
from app.config.blueprint import config_blueprint
from app.system.models.user import User


@config_blueprint.login_get("/business/list")
def config_get_business_list():
    form = GetBusinessListForm().do_validate()
    return app.restful.success(data=BusinessLine.make_pagination(form))


@config_blueprint.login_put("/business/toUser")
def config_business_to_user():
    """ 批量管理业务线与用户的关系 绑定/解除绑定 """
    form = BusinessToUserForm().do_validate()
    BusinessLine.business_to_user(form.business_list.data, form.user_list.data, form.command.data)
    return app.restful.success("修改成功")


@config_blueprint.login_get("/business")
def config_get_business():
    """ 获取业务线 """
    form = GetBusinessForm().do_validate()
    return app.restful.success("获取成功", data=form.business.to_dict())


@config_blueprint.login_post("/business")
def config_add_business():
    """ 新增业务线 """
    form = PostBusinessForm().do_validate()
    form.num.data = BusinessLine.get_insert_num()
    business = BusinessLine().create(form.data)

    # 给创建者添加绑定关系，并生成新的token
    user = User.get_first(id=g.user_id)
    user_business_list = user.loads(user.business_list)
    user_business_list.append(business.id)
    user.business_list = user_business_list
    user.update({"business_list": user.business_list})

    # 重新生成token
    token = user.generate_reset_token(g.api_permissions)
    return app.restful.success("新增成功", data={"token": token, "business_id": user_business_list})


@config_blueprint.login_put("/business")
def config_change_business():
    """ 修改业务线 """
    form = PutBusinessForm().do_validate()
    form.business.update(form.data)
    return app.restful.success("修改成功", data=form.business.to_dict())


@config_blueprint.login_delete("/business")
def config_delete_business():
    """ 删除业务线 """
    form = DeleteBusinessForm().do_validate()
    form.business.delete()
    return app.restful.success("删除成功")
