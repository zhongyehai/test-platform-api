# -*- coding: utf-8 -*-

from app.baseModel import BaseModel, db


class SwaggerDiffRecord(BaseModel):
    """ yapi数据比对记录 """
    __tablename__ = 'swagger_diff_record'

    name = db.Column(db.String(255), comment='比对标识，全量比对，或者具体分组的比对')
    is_changed = db.Column(db.Integer, default=0, comment='对比结果，1有改变，0没有改变')
    diff_summary = db.Column(db.Text, comment='比对结果数据')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get('name'):
            filters.append(SwaggerDiffRecord.name.like(f'%{attr.get("name")}%'))
        if attr.get('create_user'):
            filters.append(SwaggerDiffRecord.create_user == attr.get('create_user'))
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            filters=filters,
            order_by=cls.created_time.desc())


class SwaggerPullLog(BaseModel):
    """ swagger拉取日志 """
    __tablename__ = 'swagger_pull_log'

    is_success = db.Column(db.Integer, default=1, comment='拉取结果，0失败，1拉取中，2拉取成功')
    project_id = db.Column(db.Integer, comment='服务id')
    desc = db.Column(db.Text, comment='备注')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            order_by=cls.created_time.desc())

    def pull_fail(self, project, desc=None):
        """ 拉取失败 """
        self.update({"is_success": 0, 'desc': desc})
        project.last_pull_is_fail()

    def pull_success(self, project):
        """ 拉取成功 """
        self.update({"is_success": 2})
        project.last_pull_is_success()
