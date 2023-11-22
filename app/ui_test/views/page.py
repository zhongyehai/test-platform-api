# -*- coding: utf-8 -*-
from flask import current_app as app

from ..blueprint import ui_test
from ..model_factory import WebUiElement as Element, WebUiPage as Page
from ..forms.page import AddPageForm, EditPageForm, DeletePageForm, GetPageListForm, GetPageForm
from ...base_form import ChangeSortForm


@ui_test.login_get("/page/list")
def ui_get_page_list():
    """ 根据模块获取页面列表 """
    form = GetPageListForm()
    if form.detail:
        get_filed = [Page.id, Page.name, Page.addr, Page.module_id, Page.project_id]
    else:
        get_filed = Page.get_simple_filed_list()
    return app.restful.get_success(Page.make_pagination(form, get_filed=get_filed))


@ui_test.login_put("/page/sort")
def ui_change_sort():
    """ 更新页面的排序 """
    form = ChangeSortForm()
    Page.change_sort(**form.model_dump())
    return app.restful.change_success()


@ui_test.login_post("/page/copy")
def ui_copy_page():
    """ 复制页面 """
    form = GetPageForm()
    page = form.page.to_dict()
    page["name"] = page["name"] + "_copy"
    new_page = Page.model_create_and_get(page)
    Element.copy_element(form.id, new_page.id)
    return app.restful.copy_success({"page": new_page.to_dict()})


@ui_test.login_get("/page")
def ui_get_page():
    """ 获取页面 """
    form = GetPageForm()
    return app.restful.get_success(form.page.to_dict())


@ui_test.login_post("/page")
def ui_add_page():
    """ 新增页面 """
    form = AddPageForm()
    if len(form.page_list) == 1:
        return app.restful.success(f"页面新建成功", data=Page.model_create_and_get(form.page_list[0]).to_dict())
    Page.model_batch_create(form.page_list)
    return app.restful.add_success()


@ui_test.login_put("/page")
def ui_change_page():
    """ 修改页面 """
    form = EditPageForm()
    Page.query.filter_by(id=form.id).update(form.model_dump())
    return app.restful.change_success()


@ui_test.login_delete("/page")
def ui_delete_page():
    """ 删除页面 """
    form = DeletePageForm()
    Page.delete_by_id(form.id)
    return app.restful.delete_success()
