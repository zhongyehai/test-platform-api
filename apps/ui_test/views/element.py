# -*- coding: utf-8 -*-
from flask import request, current_app as app, send_from_directory, g

from config import find_element_option
from ..blueprint import ui_test
from ...base_form import ChangeSortForm
from ..model_factory import WebUiProject as Project, WebUiModule as Module, WebUiPage as Page, WebUiElement as Element
from ..forms.element import AddElementForm, EditElementForm, DeleteElementForm, GetElementListForm, \
    GetElementForm, ChangeElementByIdForm
from utils.parse.parse_excel import parse_file_content
from utils.util.file_util import STATIC_ADDRESS


@ui_test.login_get("/element/list")
def ui_get_element_list():
    """ 查元素list """
    form = GetElementListForm()
    if form.detail:
        get_filed = [Element.id, Element.name, Element.by, Element.element, Element.wait_time_out, Element.page_id]
    else:
        get_filed = Element.get_simple_filed_list()
    return app.restful.get_success(Element.make_pagination(form, get_filed=get_filed))


@ui_test.login_put("/element/sort")
def ui_change_element_sort():
    """ 更新元素的排序 """
    form = ChangeSortForm()
    Element.change_sort(**form.model_dump())
    return app.restful.change_success()


@ui_test.login_put("/element/id")
def ui_change_element_by_id():
    """ 根据id更新元素 """
    form = ChangeElementByIdForm()
    Element.query.filter_by(id=form.id).update(form.model_dump())
    return app.restful.change_success()


@ui_test.login_get("/element/from")
def ui_get_element_from():
    """ 获取元素的归属信息 """
    form = GetElementForm()
    project = Project.get_first(id=form.element.project_id)
    module_name = Module.get_from_path(form.element.module_id)
    page = Page.get_first(id=form.element.page_id)
    res_msg = f'此元素归属：【{project.name}_{module_name}_{page.name}_{form.element.name}】'
    return app.restful.get_success(res_msg)


@ui_test.login_get("/element/template/download")
def ui_get_element_template():
    """ 下载元素导入模板 """
    return send_from_directory(STATIC_ADDRESS, "element_upload_template.xls", as_attachment=True)


@ui_test.post("/element/upload")
def ui_upload_element():
    """ 从excel中导入元素 """
    file, page, user_id = request.files.get("file"), Page.get_first(id=request.form.get("id")), g.user_id
    if not page:
        return app.restful.fail("页面不存在")
    if file and file.filename.endswith("xls"):
        # [{"元素名称": "账号输入框", "定位方式": "根据id属性定位", "元素表达式": "account", "等待元素出现的超时时间": 10.0}]
        excel_data = parse_file_content(file.read())
        option_dict = {option["label"]: option["value"] for option in find_element_option}
        with Element.db.auto_commit():
            element_list = []
            for element_data in excel_data:
                name, by = element_data.get("元素名称"), element_data.get("定位方式")
                element, wait_time_out = element_data.get("元素表达式"), element_data.get("等待元素出现的超时时间")
                if all((name, by, element, wait_time_out)):
                    new_element = Element()
                    new_element.name = name
                    new_element.by = option_dict[by] if by in option_dict else "id"
                    new_element.element = element
                    new_element.wait_time_out = wait_time_out
                    new_element.project_id = page.project_id
                    new_element.module_id = page.module_id
                    new_element.page_id = page.id
                    new_element.create_user = new_element.update_user = g.user_id
                    element_list.append(new_element)
                Element.db.session.add_all(element_list)
        return app.restful.upload_success()
    return app.restful.fail("请上传后缀为xls的Excel文件")


@ui_test.login_get("/element")
def ui_get_element():
    """ 获取元素 """
    form = GetElementForm()
    return app.restful.get_success(form.element.to_dict())


@ui_test.login_post("/element")
def ui_add_element():
    """ 新增元素 """
    form = AddElementForm()
    if form.element_list == 1:
        return app.restful.add_success(Element.model_create_and_get(form.element_list[0]).to_dict())
    Element.model_batch_create(form.element_list)
    form.update_page_addr()
    return app.restful.add_success()


@ui_test.login_put("/element")
def ui_change_element():
    """ 修改元素 """
    form = EditElementForm()
    Element.query.filter_by(id=form.id).update(form.model_dump())
    form.update_page_addr()
    return app.restful.change_success()


@ui_test.login_delete("/element")
def ui_delete_element():
    """ 删除元素 """
    form = DeleteElementForm()
    Element.delete_by_id(form.id)
    return app.restful.delete_success()
