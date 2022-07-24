# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class ConfigType(BaseModel):
    """ 配置类型表 """

    __tablename__ = 'config_type'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='字段名')
    desc = db.Column(db.Text(), comment='描述')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )


class Config(BaseModel):
    """ 配置表 """

    __tablename__ = 'config'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='字段名')
    value = db.Column(db.Text(), nullable=True, comment='字段值')
    type = db.Column(db.Integer(), nullable=True, comment='配置类型')
    desc = db.Column(db.Text(), comment='描述')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.type.data:
            filters.append(cls.type == form.type.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )
