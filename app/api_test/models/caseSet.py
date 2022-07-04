# -*- coding: utf-8 -*-

from app.api_test.models.case import ApiCase as Case
from app.baseModel import BaseCaseSet, db


class ApiSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False

    __tablename__ = 'api_test_case_set'

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
