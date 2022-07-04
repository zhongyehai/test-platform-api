# -*- coding: utf-8 -*-

from flask import request
from flask_login import current_user

from app.utils import restful
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseView import BaseMethodView
from app.ui_test.models.element import UiElement
from app.ui_test.models.page import UiPage, db
from app.ui_test.forms.page import AddPageForm, EditPageForm, DeletePageForm, PageListForm, GetPageById


@ui_test.route('/page/list', methods=['GET'])
@login_required
def get_page_list():
    """ 根据模块查接口list """
    form = PageListForm()
    if form.validate():
        return restful.success(data=UiPage.make_pagination(form))


@ui_test.route('/page/copy', methods=['post'])
@login_required
def copy_page():
    """ 复制页面 """
    form = GetPageById()
    if form.validate():
        page = form.page.to_dict()

        # 复制页面
        page['num'] = UiPage.get_insert_num(module_id=page['module_id'])
        page['name'] = page['name'] + '_copy'
        page['create_user'] = page['update_user'] = current_user.id
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
                    create_user=current_user.id,
                    update_user=current_user.id
                ))

                # num = db.Column(db.Integer(), nullable=True, comment='序号')
                # name = db.Column(db.String(255), nullable=True, comment='名称')
                # desc = db.Column(db.Text(), default='', nullable=True, comment='描述')
                # by = db.Column(db.String(255), nullable=True, comment='定位方式')
                # element = db.Column(db.Text(), default='', nullable=True, comment='元素值')
                # page_id = db.Column(db.Integer(), db.ForeignKey('ui_test_page.id'), comment='所属的页面id')
                # module_id = db.Column(db.Integer(), db.ForeignKey('ui_test_module.id'), comment='所属的模块id')
                # project_id = db.Column(db.Integer(), db.ForeignKey('ui_test_project.id'), nullable=True, comment='所属的项目id')

        return restful.success(msg='复制成功', data={
            "page": new_page.to_dict(),
            "element": [element.to_dict() for element in UiElement.get_all(page_id=new_page.id)]
        })
    return restful.fail(form.get_error())


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
            return restful.success(data=form.page.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddPageForm()
        if form.validate():
            form.num.data = UiPage.get_insert_num(module_id=form.module_id.data)
            new_page = UiPage().create(form.data)
            return restful.success(f'页面【{form.name.data}】新建成功', data=new_page.to_dict())
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
            form.page.delete()
            return restful.success(f'页面【{form.page.name}】删除成功')
        return restful.fail(form.get_error())


ui_test.add_url_rule('/page', view_func=UiPageView.as_view('ui_page'))
