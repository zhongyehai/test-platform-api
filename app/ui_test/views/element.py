# -*- coding: utf-8 -*-

from flask import request

from app.utils import restful
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from app.ui_test.models.element import UiElement
from app.ui_test.forms.element import AddElementForm, EditElementForm, DeleteElementForm, ElementListForm, GetElementById, \
    ChangeElementById


@ui_test.route('/element/list', methods=['GET'])
@login_required
def get_element_list():
    """ 根据模块查接口list """
    form = ElementListForm()
    if form.validate():
        return restful.success(data=UiElement.make_pagination(form))


@ui_test.route('/element/sort', methods=['put'])
@login_required
def change_element_sort():
    """ 更新接口的排序 """
    UiElement.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


@ui_test.route('/element/changeById', methods=['put'])
@login_required
def change_element_by_id():
    """ 根据id更新元素 """
    form = ChangeElementById()
    if form.validate():
        form.old.update(form.data)
        return restful.success(f'元素修改成功')
    return restful.fail(form.get_error())


class UiElementView(BaseMethodView):
    """ 接口信息 """

    def get(self):
        form = GetElementById()
        if form.validate():
            return restful.success(data=form.element.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddElementForm()
        if form.validate():
            form.num.data = UiElement.get_insert_num(module_id=form.module_id.data)
            new_element = UiElement().create(form.data)
            form.update_page_addr()
            return restful.success(f'元素【{form.name.data}】新建成功', data=new_element.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditElementForm()
        if form.validate():
            form.old.update(form.data)
            form.update_page_addr()
            return restful.success(f'元素【{form.name.data}】修改成功', form.old.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteElementForm()
        if form.validate():
            form.element.delete()
            return restful.success(f'元素【{form.element.name}】删除成功')
        return restful.fail(form.get_error())


ui_test.add_url_rule('/element', view_func=UiElementView.as_view('ui_element'))
