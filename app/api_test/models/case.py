# -*- coding: utf-8 -*-

from app.baseModel import BaseCase, db
from app.api_test.models.step import ApiStep as Step


class ApiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False

    __tablename__ = 'api_test_case'

    headers = db.Column(db.Text(), comment='用例级的头部信息')
    set_id = db.Column(db.Integer, db.ForeignKey('api_test_case_set.id'), comment='所属的用例集id')

    def delete_current_and_step(self):
        for step in Step.get_all(case_id=self.id):
            step.delete()
            step.subtract_api_quote_count()
        self.delete()
        # return self.delete_current_and_children(ApiStep, 'case_id')
