# -*- coding: utf-8 -*-

from app.baseModel import BaseApi, db


class UiPage(BaseApi):
    """ 页面表 """
    __abstract__ = False

    __tablename__ = 'ui_test_page'

    addr = db.Column(db.String(255), nullable=True, comment='地址')

    module_id = db.Column(db.Integer(), db.ForeignKey('ui_test_module.id'), comment='所属的模块id')
    project_id = db.Column(db.Integer(), nullable=True, comment='所属的项目id')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(UiPage.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(UiPage.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=UiPage.num.asc()
        )
