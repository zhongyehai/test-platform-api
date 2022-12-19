# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView, AdminRequiredView
from app.system.models.business import BusinessLine
from app.system.forms.business import (
    GetBusinessForm, DeleteBusinessForm, PostBusinessForm, PutBusinessForm, GetBusinessListForm
)
from app.system.blueprint import system_manage


class GetBusinessListView(LoginRequiredView):

    def get(self):
        form = GetBusinessListForm().do_validate()
        return app.restful.success(data=BusinessLine.make_pagination(form))


class BusinessView(AdminRequiredView):

    def get(self):
        """ 获取配置类型 """
        form = GetBusinessForm().do_validate()
        return app.restful.success("获取成功", data=form.conf.to_dict())

    def post(self):
        """ 新增配置类型 """
        form = PostBusinessForm().do_validate()
        business = BusinessLine().create(form.data)
        return app.restful.success("新增成功", data=business.to_dict())

    def put(self):
        """ 修改配置类型 """
        form = PutBusinessForm().do_validate()
        form.business.update(form.data)
        return app.restful.success("修改成功", data=form.business.to_dict())

    def delete(self):
        """ 删除配置类型 """
        form = DeleteBusinessForm().do_validate()
        form.business.delete()
        return app.restful.success("删除成功")


system_manage.add_url_rule("/business", view_func=BusinessView.as_view("BusinessView"))
system_manage.add_url_rule("/business/list", view_func=GetBusinessListView.as_view("GetBusinessListView"))
