# -*- coding: utf-8 -*-
from ..case.models import ApiCase as Case
from app.baseModel import BaseModel, db


class ApiSet(BaseModel):
    """ 用例集表 """
    __tablename__ = 'api_test_case_set'

    name = db.Column(db.String(255), nullable=True, comment='用例集名称')
    num = db.Column(db.Integer(), nullable=True, comment='用例集在对应服务下的序号')
    level = db.Column(db.Integer(), nullable=True, default=2, comment='用例集级数')
    parent = db.Column(db.Integer(), nullable=True, default=None, comment='上一级用例集id')
    yapi_id = db.Column(db.Integer(), comment='当前用例集在yapi平台对应的服务id')

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='所属的服务id')
    project = db.relationship('ApiProject', backref='api_test_set')  # 一对多

    cases = db.relationship('ApiCase', order_by='ApiCase.num.asc()', lazy='dynamic')

    @classmethod
    def get_case_id(cls, project_id: int, set_id: list, case_id: list):
        """
        获取要执行的用例的id
        1.如果有用例id，则只拿对应的用例
        2.如果没有用例id，有模块id，则拿模块下的所有用例id
        3.如果没有用例id，也没有用模块id，则拿服务下所有模块下的所有用例
        """
        if len(case_id) != 0:
            return case_id
        elif len(set_id) != 0:
            set_ids = set_id
        else:
            set_ids = [
                set.id for set in cls.query.filter_by(project_id=project_id).order_by(ApiSet.num.asc()).all()
            ]
        case_ids = [
            case.id for set_id in set_ids for case in Case.query.filter_by(
                set_id=set_id,
                is_run=1
            ).order_by(Case.num.asc()).all() if case and case.is_run
        ]
        return case_ids

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.projectId.data:
            filters.append(cls.project_id == form.projectId.data)
        if form.name.data:
            filters.append(cls.name == form.name.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
