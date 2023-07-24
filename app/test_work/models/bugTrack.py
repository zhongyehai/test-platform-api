# -*- coding: utf-8 -*-
from flask import g

from app.baseModel import BaseModel, db


class BugTrack(BaseModel):
    """ 生产Bug跟踪表 """
    __tablename__ = "test_work_bug_track"
    __table_args__ = {"comment": "生产Bug跟踪表"}

    business_id = db.Column(db.Integer(), comment="业务线id")
    name = db.Column(db.String(255), default='', comment="bug名")
    detail = db.Column(db.Text(), default='', comment="bug详情")
    iteration = db.Column(db.String(128), default='', comment="迭代")
    bug_from = db.Column(db.String(128), default='', comment="缺陷来源")
    trigger_time = db.Column(db.String(128), default='', comment="发现时间")
    manager = db.Column(db.Integer(), default='', comment="跟进负责人")
    reason = db.Column(db.String(128), default='', comment="原因")
    solution = db.Column(db.String(128), default='', comment="解决方案")
    status = db.Column(db.String(64), default='todo', comment="bug状态，todo：待解决、doing：解决中、done：已解决")
    replay = db.Column(db.Integer(), default=0, comment="是否复盘，0：未复盘，1：已复盘")
    conclusion = db.Column(db.Text(), default='', comment="复盘结论")
    num = db.Column(db.Integer(), default=0, comment="序号")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.get("business_list"):
            business_list = set(form.get("business_list")) & set(g.business_list)  # 取并集
            filters.append(cls.business_id == business_list)
        else:
            if cls.is_not_admin():  # 非管理员则校验业务线权限
                filters.append(cls.business_id.in_(g.business_list))
        if form.get("name"):
            filters.append(cls.name.like(f'%{form.get("name")}%'))
        if form.get("detail"):
            filters.append(cls.detail.like(f'%{form.get("detail")}%'))
        if form.get("status"):
            filters.append(cls.status.in_(form.get("status")))
        if form.get("replay"):
            filters.append(cls.replay == form.get("replay"))
        if form.get("conclusion"):
            filters.append(cls.conclusion.like(f'%{form.get("conclusion")}%'))
        if form.get("iteration"):
            filters.append(cls.iteration.in_(form.get("iteration")))

        return cls.pagination(
            page_num=form.get("page_num"),
            page_size=form.get("page_size"),
            filters=filters,
            order_by=cls.num.asc()
        )
