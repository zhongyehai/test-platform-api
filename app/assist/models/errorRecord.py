# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class FuncErrorRecord(BaseModel):
    """ 自定义函数执行错误记录表 """
    __tablename__ = 'func_error_record'

    name = db.Column(db.String(255), nullable=True, comment='错误title')
    detail = db.Column(db.Text(), default='', comment='错误详情')

    def to_dict(self, *args, **kwargs):
        """ 自定义序列化器，把模型的每个字段转为字典，方便返回给前端 """
        return super(FuncErrorRecord, self).to_dict()

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(FuncErrorRecord.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc())
