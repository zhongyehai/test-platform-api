#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
from flask import request

from app.utils import restful
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from ..page.models import UiPage
from .forms import AddPageForm, EditPageForm, DeletePageForm, PageListForm, GetPageById


@ui_test.route('/page/list', methods=['GET'])
@login_required
def get_page_list():
    """ 根据模块查接口list """
    form = PageListForm()
    if form.validate():
        return restful.success(data=UiPage.make_pagination(form))


@ui_test.route('/page/sort', methods=['put'])
@login_required
def change_page_sort():
    """ 更新接口的排序 """
    UiPage.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


class UiPageView(BaseMethodView):
    """ 接口信息 """

    def get(self):
        form = GetPageById()
        if form.validate():
            return restful.success(data=form.api.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddPageForm()
        if form.validate():
            form.num.data = UiPage.get_insert_num(module_id=form.module_id.data)
            new_api = UiPage().create(form.data)
            return restful.success(f'页面【{form.name.data}】新建成功', data=new_api.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditPageForm()
        if form.validate():
            form.old.update(form.data)
            return restful.success(f'页面【{form.name.data}】修改成功', form.old.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeletePageForm()
        if form.validate():
            form.api.delete()
            return restful.success(f'页面【{form.api.name}】删除成功')
        return restful.fail(form.get_error())


ui_test.add_url_rule('/page', view_func=UiPageView.as_view('ui_page'))
