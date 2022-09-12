# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class UserOperationLog(BaseModel):
    """ 用户操作记录表 """
    __tablename__ = 'system_user_operation_log'

    ip = db.Column(db.String(256), nullable=True, comment='访问来源ip')
    url = db.Column(db.String(256), nullable=True, comment='请求地址')
    method = db.Column(db.String(10), nullable=True, comment='请求方法')
    headers = db.Column(db.Text, nullable=True, comment='头部参数')
    params = db.Column(db.String(256), nullable=True, comment='查询字符串参数')
    data_form = db.Column(db.Text, nullable=True, comment='form_data参数')
    data_json = db.Column(db.Text, nullable=True, comment='json参数')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.url.data:
            filters.append(cls.url == form.url.data)
        if form.method.data:
            filters.append(cls.method == form.method.data)
        if form.request_user.data:
            filters.append(cls.create_user == form.request_user.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.desc()
        )
