# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.element import AppUiElement as Element
from app.app_ui_test.models.page import AppUiPage as Page, db
from app.app_ui_test.forms.page import AddPageForm, EditPageForm, DeletePageForm, PageListForm, GetPageById


class AppUiGetPageListView(LoginRequiredView):

    def get(self):
        """ 根据模块获取页面列表 """
        form = PageListForm().do_validate()
        return app.restful.success(data=Page.make_pagination(form))


class AppUiCopyPageView(LoginRequiredView):

    def post(self):
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


class AppUiChangePageSortView(LoginRequiredView):

    def put(self):
        """ 更新接口的排序 """
        Page.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppUiPageView(LoginRequiredView):

    def get(self):
        """ 获取页面 """
        form = GetPageById().do_validate()
        return app.restful.success(data=form.page.to_dict())

    def post(self):
        """ 新增页面 """
        form = AddPageForm().do_validate()
        form.num.data = Page.get_insert_num(module_id=form.module_id.data)
        new_page = Page().create(form.data)
        return app.restful.success(f"页面【{form.name.data}】新建成功", data=new_page.to_dict())

    def put(self):
        """ 修改页面 """
        form = EditPageForm().do_validate()
        form.old.update(form.data)
        return app.restful.success(f"页面【{form.name.data}】修改成功", form.old.to_dict())

    def delete(self):
        """ 删除页面 """
        form = DeletePageForm().do_validate()
        form.page.delete()
        return app.restful.success(f"页面【{form.page.name}】删除成功")


app_ui_test.add_url_rule("/page", view_func=AppUiPageView.as_view("AppUiPageView"))
app_ui_test.add_url_rule("/page/copy", view_func=AppUiCopyPageView.as_view("AppUiCopyPageView"))
app_ui_test.add_url_rule("/page/list", view_func=AppUiGetPageListView.as_view("AppUiGetPageListView"))
app_ui_test.add_url_rule("/page/sort", view_func=AppUiChangePageSortView.as_view("AppUiChangePageSortView"))
