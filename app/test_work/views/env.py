# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import LoginRequiredView, NotLoginView
from app.test_work.blueprint import test_work
from app.test_work.forms.env import GetEnvListForm, GetEnvForm, DeleteEnvForm, AddEnvForm, \
    ChangeEnvForm
from app.test_work.models.env import Env


class GetEnvListView(NotLoginView):

    def post(self):
        """ 获取数据列表 """
        form = GetEnvListForm()
        return app.restful.success("获取成功", data=Env.make_pagination(form.data))


class EnvView(LoginRequiredView):
    """ 测试数据管理 """

    def get(self):
        """ 获取数据 """
        form = GetEnvForm().do_validate()
        return app.restful.success("获取成功", data=form.env.to_dict())

    def post(self):
        """ 新增数据 """
        form = AddEnvForm().do_validate()
        form_data = form.data
        for data in form_data.pop("data_list"):
            form_data["num"] = Env.get_insert_num()
            form_data.update(data)
            Env().create(form_data)
        return app.restful.success("新增成功")

    def put(self):
        """ 修改数据 """
        form = ChangeEnvForm().do_validate()
        form.env.update(form.data)
        return app.restful.success("修改成功", data=form.env.to_dict())

    def delete(self):
        """ 删除数据 """
        form = DeleteEnvForm().do_validate()
        form.env.delete()
        return app.restful.success("删除成功")


test_work.add_url_rule("/env", view_func=EnvView.as_view("EnvView"))
test_work.add_url_rule("/env/list", view_func=GetEnvListView.as_view("GetEnvListView"))
