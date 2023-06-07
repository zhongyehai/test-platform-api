# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class JobRunLog(BaseModel):
    """ 系统job执行记录 """
    __tablename__ = "system_job_run_log"
    __table_args__ = {"comment": "系统job执行记录"}

    func_name = db.Column(db.String(255), comment="执行方法")
    status = db.Column(db.Integer(), default=1, comment="执行状态：0失败、1执行中、2执行成功")
    business_id = db.Column(db.Integer(), default=None, comment="业务线id")
    detail = db.Column(db.Text, default=None, comment="执行结果数据")

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get("func_name"):
            filters.append(cls.func_name == attr.get("func_name"))
        return cls.pagination(
            page_num=attr.get("pageNum", 1),
            page_size=attr.get("pageSize", 20),
            filters=filters,
            order_by=cls.created_time.desc())

    def run_fail(self, detail=None):
        """ 执行失败 """
        self.update({"status": 0, "detail": self.dumps(detail)})

    def run_success(self, detail):
        """ 执行成功 """
        self.update({"status": 2, "detail": self.dumps(detail)})
