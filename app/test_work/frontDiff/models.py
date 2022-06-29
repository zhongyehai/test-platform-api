# -*- coding: utf-8 -*-

from app.baseModel import BaseModel, db


class FrontDiffRecord(BaseModel):
    """ 前端引用接口数据比对记录 """
    __tablename__ = 'test_work_front_diff_record'
    parent = db.Column(db.String(255), comment='父级文件夹')
    name = db.Column(db.String(255), comment='当前文件')
    is_changed = db.Column(db.Integer, default=0, comment='对比结果，1有改变，0没有改变')
    diff_summary = db.Column(db.Text, comment='比对结果数据')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get('name'):
            filters.append(FrontDiffRecord.name.like(f'%{attr.get("name")}%'))
        if attr.get('create_user'):
            filters.append(FrontDiffRecord.create_user == attr.get('create_user'))
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            filters=filters,
            order_by=cls.created_time.desc())
