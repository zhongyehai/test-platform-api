# -*- coding: utf-8 -*-

from app.baseModel import BaseApi, db


class UiElement(BaseApi):
    """ 页面元素表 """
    __abstract__ = False

    __tablename__ = 'ui_test_element'

    by = db.Column(db.String(255), nullable=True, comment='定位方式')
    element = db.Column(db.Text(), default='', nullable=True, comment='元素值')

    page_id = db.Column(db.Integer(), db.ForeignKey('ui_test_page.id'), comment='所属的页面id')
    module_id = db.Column(db.Integer(), db.ForeignKey('ui_test_module.id'), comment='所属的模块id')
    project_id = db.Column(db.Integer(), db.ForeignKey('ui_test_project.id'), nullable=True, comment='所属的项目id')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.pageId.data:
            filters.append(UiElement.page_id == form.pageId.data)
        if form.name.data:
            filters.append(UiElement.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=UiElement.num.asc()
        )
