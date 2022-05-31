# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class ApiModule(BaseModel):
    """ 模块表 """
    __tablename__ = 'api_test_module'
    name = db.Column(db.String(255), nullable=True, comment='模块名')
    num = db.Column(db.Integer(), nullable=True, comment='模块在对应服务下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='模块级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级模块id')
    yapi_id = db.Column(db.Integer(), comment='当前模块在yapi平台对应的模块id')

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='modules')  # 一对多

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
