# -*- coding: utf-8 -*-
from flask import request, current_app as app, send_from_directory, g

from app.baseView import LoginRequiredView, NotLoginView
from app.busines import ElementBusiness
from app.config.models.config import Config
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.project import AppUiProject as Project
from app.app_ui_test.models.module import AppUiModule as Module
from app.app_ui_test.models.page import AppUiPage as Page, db
from app.app_ui_test.models.element import AppUiElement as Element
from app.app_ui_test.forms.element import AddElementForm, EditElementForm, DeleteElementForm, ElementListForm, \
    GetElementById, ChangeElementById
from utils.parse.parseExcel import parse_file_content
from utils.util.fileUtil import STATIC_ADDRESS


class AppUiGetElementListView(LoginRequiredView):

    def get(self):
        """ 根据模块查接口list """
        form = ElementListForm().do_validate()
        return app.restful.success(data=Element.make_pagination(form))


class AppUiChangeElementSortView(LoginRequiredView):

    def put(self):
        """ 更新接口的排序 """
        Element.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppUiChangeElementByIdView(LoginRequiredView):

    def put(self):
        """ 根据id更新元素 """
        form = ChangeElementById().do_validate()
        form.old.update(form.data)
        return app.restful.success(f"元素修改成功")


class ElementGetElementFromView(LoginRequiredView):

    def get(self):
        """ 根据元素id归属信息 """
        form = GetElementById().do_validate()
        project = Project.get_first(id=form.element.project_id)
        module_name = Module.get_from_path(form.element.module_id)
        page = Page.get_first(id=form.element.page_id)
        res_msg = f'此元素归属：【{project.name}_{module_name}_{page.name}_{form.element.name}】'
        return app.restful.success(msg=res_msg)


class ElementTemplateDownloadView(LoginRequiredView):

    def get(self):
        """ 下载元素导入模板 """
        return send_from_directory(STATIC_ADDRESS, "元素导入模板.xls", as_attachment=True)


class ElementUploadView(NotLoginView):

    def post(self):
        """ 从excel中导入元素 """
        file, page, user_id = request.files.get("file"), Page.get_first(id=request.form.get("id")), g.user_id
        if not page:
            return app.restful.fail("页面不存在")
        if file and file.filename.endswith("xls"):
            # [{"元素名称": "账号输入框", "定位方式": "根据id属性定位", "元素表达式": "account", "等待元素出现的超时时间": 10.0}]
            excel_data = parse_file_content(file.read())
            option_dict = {option["label"]: option["value"] for option in Config.get_find_element_option()}
            with db.auto_commit():
                for element_data in excel_data:
                    name, by = element_data.get("元素名称"), element_data.get("定位方式")
                    element, wait_time_out = element_data.get("元素表达式"), element_data.get("等待元素出现的超时时间")
                    if all((name, by, element, wait_time_out)):
                        new_element = Element()
                        new_element.name = name
                        new_element.by = option_dict[by] if by in option_dict else "id"
                        new_element.element = element
                        new_element.wait_time_out = wait_time_out
                        new_element.num = new_element.get_insert_num(page_id=page.id)
                        new_element.project_id = page.project_id
                        new_element.module_id = page.module_id
                        new_element.page_id = page.id
                        new_element.create_user = user_id
                        db.session.add(new_element)
            return app.restful.success("元素导入成功")
        return app.restful.fail("请上传后缀为xls的Excel文件")


class AppUiElementView(LoginRequiredView):

    def get(self):
        """ 获取元素 """
        form = GetElementById().do_validate()
        return app.restful.success(data=form.element.to_dict())

    def post(self):
        """ 新增元素 """
        form = AddElementForm().do_validate()
        element_list = ElementBusiness.post(form, Element)
        return app.restful.success(f"元素新建成功", data=element_list[0].to_dict() if len(element_list) == 1 else None)

    def put(self):
        """ 修改元素 """
        form = EditElementForm().do_validate()
        form.old.update(form.data)
        return app.restful.success(f"元素【{form.name.data}】修改成功", form.old.to_dict())

    def delete(self):
        """ 删除元素 """
        form = DeleteElementForm().do_validate()
        form.element.delete()
        return app.restful.success(f"元素【{form.element.name}】删除成功")


app_ui_test.add_url_rule("/element", view_func=AppUiElementView.as_view("AppUiElementView"))
app_ui_test.add_url_rule("/element/upload", view_func=ElementUploadView.as_view("ElementUploadView"))
app_ui_test.add_url_rule("/element/list", view_func=AppUiGetElementListView.as_view("AppUiGetElementListView"))
app_ui_test.add_url_rule("/element/sort", view_func=AppUiChangeElementSortView.as_view("AppUiChangeElementSortView"))
app_ui_test.add_url_rule("/element/from", view_func=ElementGetElementFromView.as_view("ElementGetElementFromView"))
app_ui_test.add_url_rule("/element/changeById",
                         view_func=AppUiChangeElementByIdView.as_view("AppUiChangeElementByIdView"))
app_ui_test.add_url_rule("/element/template/download",
                         view_func=ElementTemplateDownloadView.as_view("ElementTemplateDownloadView"))
