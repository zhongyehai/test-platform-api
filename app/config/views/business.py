# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView, AdminRequiredView
from app.config.models.business import BusinessLine
from app.config.forms.business import (
    GetBusinessForm, DeleteBusinessForm, PostBusinessForm, PutBusinessForm, GetBusinessListForm, BusinessToUserForm
)
from app.config.blueprint import config_blueprint


class GetBusinessListView(LoginRequiredView):

    def get(self):
        form = GetBusinessListForm().do_validate()
        return app.restful.success(data=BusinessLine.make_pagination(form))


class BusinessToUser(LoginRequiredView):
    """ 批量管理业务线与用户的关系 绑定/解除绑定 """

    def put(self):
        form = BusinessToUserForm().do_validate()
        BusinessLine.business_to_user(form.business_list.data, form.user_list.data, form.command.data)
        return app.restful.success("修改成功")

class BusinessView(LoginRequiredView):

    def get(self):
        """ 获取业务线 """
        form = GetBusinessForm().do_validate()
        return app.restful.success("获取成功", data=form.business.to_dict())

    def post(self):
        """ 新增业务线 """
        form = PostBusinessForm().do_validate()
        form.num.data = BusinessLine.get_insert_num()
        business = BusinessLine().create(form.data)
        return app.restful.success("新增成功", data=business.to_dict())

    def put(self):
        """ 修改业务线 """
        form = PutBusinessForm().do_validate()
        form.business.update(form.data)
        return app.restful.success("修改成功", data=form.business.to_dict())

    def delete(self):
        """ 删除业务线 """
        form = DeleteBusinessForm().do_validate()
        form.business.delete()
        return app.restful.success("删除成功")


config_blueprint.add_url_rule("/business", view_func=BusinessView.as_view("BusinessView"))
config_blueprint.add_url_rule("/business/toUser", view_func=BusinessToUser.as_view("BusinessToUser"))
config_blueprint.add_url_rule("/business/list", view_func=GetBusinessListView.as_view("GetBusinessListView"))

