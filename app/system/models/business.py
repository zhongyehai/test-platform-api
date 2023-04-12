# -*- coding: utf-8 -*-
from flask import g
from app.baseModel import BaseModel, db
from app.system.models.user import User

class BusinessLine(BaseModel):
    """ 业务线 """

    __tablename__ = "config_business"
    __table_args__ = {"comment": "业务线配置表"}

    name = db.Column(db.String(128), nullable=True, unique=True, comment="业务线名")
    code = db.Column(db.String(128), nullable=True, unique=True, comment="业务线编码")
    num = db.Column(db.Integer(), nullable=True, comment="序号")
    desc = db.Column(db.Text(), comment="描述")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if cls.is_not_admin():  # 如果用户不是管理员权限，则只返回当前用户的业务线
            filters.append(cls.id.in_(g.business_id))
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.code.data:
            filters.append(cls.code.like(f'%{form.code.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.desc()
        )
