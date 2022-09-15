# -*- coding: utf-8 -*-

from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from app.web_ui_test.models.element import WebUiElement as Element
from app.web_ui_test.forms.element import AddElementForm, EditElementForm, DeleteElementForm, ElementListForm, \
    GetElementById, ChangeElementById

ns = web_ui_test.namespace("element", description="元素管理相关接口")


@ns.route('/list/')
class WebUiGetElementListView(LoginRequiredView):

    def get(self):
        """ 根据模块查接口list """
        form = ElementListForm()
        if form.validate():
            return app.restful.success(data=Element.make_pagination(form))


@ns.route('/sort/')
class WebUiChangeElementSortView(LoginRequiredView):

    def put(self):
        """ 更新接口的排序 """
        Element.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


@ns.route('/changeById/')
class WebUiChangeElementByIdView(LoginRequiredView):

    def put(self):
        """ 根据id更新元素 """
        form = ChangeElementById()
        if form.validate():
            form.old.update(form.data)
            return app.restful.success(f'元素修改成功')
        return app.restful.fail(form.get_error())


@ns.route('/')
class WebUiElementView(LoginRequiredView):

    def get(self):
        """ 获取元素 """
        form = GetElementById()
        if form.validate():
            return app.restful.success(data=form.element.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增元素 """
        form = AddElementForm()
        if form.validate():
            form.num.data = Element.get_insert_num(module_id=form.module_id.data)
            new_element = Element().create(form.data)
            form.update_page_addr()
            return app.restful.success(f'元素【{form.name.data}】新建成功', data=new_element.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改元素 """
        form = EditElementForm()
        if form.validate():
            form.old.update(form.data)
            form.update_page_addr()
            return app.restful.success(f'元素【{form.name.data}】修改成功', form.old.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除元素 """
        form = DeleteElementForm()
        if form.validate():
            form.element.delete()
            return app.restful.success(f'元素【{form.element.name}】删除成功')
        return app.restful.fail(form.get_error())
