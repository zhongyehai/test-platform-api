# -*- coding: utf-8 -*-

from app.api_test.models.case import ApiCase as Case
from app.baseModel import BaseCaseSet, db


class ApiCaseSet(BaseCaseSet):
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
            1、即没选择用例，也没选择用例集
            2、只选择了用例
            3、只选了用例集
            4、选定了用例和用例集
        """
        # 1、只选择了用例，则直接返回用例
        if len(case_id) != 0 and len(set_id) == 0:
            return case_id

        # 2、没有选择用例集和用例，则视为选择了所有用例集
        elif len(set_id) == 0 and len(case_id) == 0:
            set_id = [
                case_set.id for case_set in cls.query.filter_by(project_id=project_id).order_by(cls.num.asc()).all()
            ]

        # 解析已选中的用例集，并继承已选中的用例列表，再根据用例id去重
        case_ids = [
            case.id for case_set_id in set_id for case in Case.query.filter_by(
                set_id=case_set_id,
                is_run=1
            ).order_by(Case.num.asc()).all() if case and case.is_run
        ]
        case_ids.extend(case_id)
        return list(set(case_ids))

    @classmethod
    def create_case_set_by_project(cls, project_id):
        """ 根据项目id，创建用例集 """
        for name in ['引用用例集', '流程用例集', '单接口用例集', '辅助测试用例集']:
            cls().create({'name': name, 'project_id': project_id})
