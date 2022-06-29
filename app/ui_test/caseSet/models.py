# -*- coding: utf-8 -*-

from ..case.models import UiCase
from app.baseModel import BaseCaseSet, db


class UiCaeSet(BaseCaseSet):
    """ 用例集表 """
    __abstract__ = False

    __tablename__ = 'ui_test_case_set'

    project_id = db.Column(db.Integer, db.ForeignKey('ui_test_project.id'), comment='所属的服务id')
    project = db.relationship('UiProject', backref='case_sets')  # 一对多

    cases = db.relationship('UiCase', order_by='UiCase.num.asc()', lazy='dynamic')

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
                set.id for set in cls.query.filter_by(project_id=project_id).order_by(UiCaeSet.num.asc()).all()
            ]
        case_ids = [
            case.id for set_id in set_ids for case in UiCase.query.filter_by(
                set_id=set_id,
                is_run=1
            ).order_by(UiCase.num.asc()).all() if case and case.is_run
        ]
        return case_ids
