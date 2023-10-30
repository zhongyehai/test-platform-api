# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.web_ui_test.blueprint import ui_test
from app.web_ui_test.models.element import WebUiElement as Element
from app.web_ui_test.models.page import WebUiPage as Page, db
from app.web_ui_test.forms.page import AddPageForm, EditPageForm, DeletePageForm, PageListForm, GetPageById


@ui_test.login_get("/page/list")
def ui_get_page_list():
    """ 根据模块获取页面列表 """
    form = PageListForm().do_validate()
    return app.restful.success(data=Page.make_pagination(form))


@ui_test.login_post("/page/copy")
def ui_copy_page():
    """ 复制页面 """
    form = GetPageById().do_validate()
    page = form.page.to_dict()

    # 复制页面
    page["num"] = Page.get_insert_num(module_id=page["module_id"])
    page["name"] = page["name"] + "_copy"
    page["create_user"] = page["update_user"] = g.user_id
    new_page = Page().create(page)

    # 复制页面元素
    with db.auto_commit():
        for index, element in enumerate(Element.get_all(page_id=page["id"])):
            element_dict = element.to_dict()
            element_dict.pop("id")
            element_dict["num"], element_dict["page_id"] = index, new_page.id
            element_dict["create_user"] = element_dict["update_user"] = g.user_id
            db.session.add(Element(**element_dict))

    return app.restful.success(msg="复制成功", data={"page": new_page.to_dict()})


@ui_test.login_put("/page/sort")
def ui_change_sort():
    """ 更新接口的排序 """
    Page.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
    return app.restful.success(msg="修改排序成功")


@ui_test.login_get("/page")
def ui_get_page():
    """ 获取页面 """
    form = GetPageById().do_validate()
    return app.restful.success(data=form.page.to_dict())


@ui_test.login_post("/page")
def ui_add_page():
    """ 新增页面 """
    form = AddPageForm().do_validate()
    for page in form.page_list.data:
        page["project_id"] = form.project_id.data
        page["module_id"] = form.module_id.data
        page["num"] = Page.get_insert_num(module_id=form.module_id.data)
        new_page = Page().create(page)
    return app.restful.success(f"页面新建成功", data=new_page.to_dict() if len(form.page_list.data) == 1 else None)


@ui_test.login_put("/page")
def ui_change_page():
    """ 修改页面 """
    form = EditPageForm().do_validate()
    form.old.update(form.data)
    return app.restful.success(f"页面【{form.name.data}】修改成功", form.old.to_dict())


@ui_test.login_delete("/page")
def ui_delete_page():
    """ 删除页面 """
    form = DeletePageForm().do_validate()
    form.page.delete()
    return app.restful.success(f"页面【{form.page.name}】删除成功")
