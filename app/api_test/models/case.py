# -*- coding: utf-8 -*-
from app.baseModel import BaseCase, db
from app.api_test.models.step import ApiStep as Step


class ApiCase(BaseCase):
    """ 用例表 """
    __abstract__ = False
    __tablename__ = "api_test_case"
    __table_args__ = {"comment": "接口测试用例表"}

    headers = db.Column(db.Text(), default='[{"key": "", "value": "", "remark": ""}]', comment="用例的头部信息")

    def delete_current_and_step(self):
        for step in Step.get_all(case_id=self.id):
            step.delete()
            step.subtract_api_quote_count()
        self.delete()
        # return self.delete_current_and_children(ApiStep, "case_id")
