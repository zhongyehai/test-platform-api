# -*- coding: utf-8 -*-

from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.web_ui_test import web_ui_test
from app.web_ui_test.models.element import UiElement
from app.web_ui_test.models.page import UiPage, db
from app.web_ui_test.forms.page import AddPageForm, EditPageForm, DeletePageForm, PageListForm, GetPageById

ns = web_ui_test.namespace("page", description="页面管理相关接口")


@ns.route('/list/')
class WebUiGetPageListView(LoginRequiredView):

    def get(self):
        """ 根据模块获取页面列表 """
        form = PageListForm()
        if form.validate():
            return app.restful.success(data=UiPage.make_pagination(form))


@ns.route('/copy/')
class WebUiCopyPageView(LoginRequiredView):

    def post(self):
        """ 复制页面 """
        form = GetPageById()
        if form.validate():
            page = form.page.to_dict()

            # 复制页面
            page['num'] = UiPage.get_insert_num(module_id=page['module_id'])
            page['name'] = page['name'] + '_copy'
            page['create_user'] = page['update_user'] = g.user_id
            new_page = UiPage().create(page)

            # 复制页面元素
            with db.auto_commit():
                for index, element in enumerate(UiElement.get_all(page_id=page['id'])):
                    element_dict = element.to_dict()
                    element_dict.pop('id')
                    # db.session.add(UiElement(**element))
                    db.session.add(UiElement(
                        num=index,
                        name=element.name,
                        desc=element.desc,
                        by=element.by,
                        element=element.element,
                        page_id=new_page.id,
                        module_id=element.module_id,
                        project_id=element.project_id,
                        created_time=element.created_time,
                        update_time=element.update_time,
                        create_user=g.user_id,
                        update_user=g.user_id
                    ))

            return app.restful.success(msg='复制成功', data={
                "page": new_page.to_dict(),
                "element": [element.to_dict() for element in UiElement.get_all(page_id=new_page.id)]
            })
        return app.restful.fail(form.get_error())


@ns.route('/sort/')
class WebUiChangePageSortView(LoginRequiredView):

    def put(self):
        """ 更新接口的排序 """
        UiPage.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
        return app.restful.success(msg='修改排序成功')


@ns.route('/')
class WebUiPageView(LoginRequiredView):

    def get(self):
        """ 获取页面 """
        form = GetPageById()
        if form.validate():
            return app.restful.success(data=form.page.to_dict())
        return app.restful.fail(form.get_error())

    def post(self):
        """ 新增页面 """
        form = AddPageForm()
        if form.validate():
            form.num.data = UiPage.get_insert_num(module_id=form.module_id.data)
            new_page = UiPage().create(form.data)
            return app.restful.success(f'页面【{form.name.data}】新建成功', data=new_page.to_dict())
        return app.restful.fail(form.get_error())

    def put(self):
        """ 修改页面 """
        form = EditPageForm()
        if form.validate():
            form.old.update(form.data)
            return app.restful.success(f'页面【{form.name.data}】修改成功', form.old.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除页面 """
        form = DeletePageForm()
        if form.validate():
            form.page.delete()
            return app.restful.success(f'页面【{form.page.name}】删除成功')
        return app.restful.fail(form.get_error())
