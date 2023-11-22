# -*- coding: utf-8 -*-
from flask import g

from app.base_model import BaseModel, db


class BugTrack(BaseModel):
    """ 生产Bug跟踪表 """
    __tablename__ = "test_work_bug_track"
    __table_args__ = {"comment": "生产Bug跟踪表"}

    business_id = db.Column(db.Integer(), index=True, comment="业务线id")
    name = db.Column(db.String(255), default='', comment="bug名")
    detail = db.Column(db.Text(), default='', comment="bug详情")
    iteration = db.Column(db.String(128), default='', comment="迭代")
    bug_from = db.Column(db.String(128), default='', comment="缺陷来源")
    trigger_time = db.Column(db.String(128), default='', comment="发现时间")
    manager = db.Column(db.Integer(), default=None, comment="跟进负责人")
    reason = db.Column(db.String(128), default='', comment="原因")
    solution = db.Column(db.String(128), default='', comment="解决方案")
    status = db.Column(db.String(64), default='todo', comment="bug状态，todo：待解决、doing：解决中、done：已解决")
    replay = db.Column(db.Integer(), default=0, comment="是否复盘，0：未复盘，1：已复盘")
    conclusion = db.Column(db.Text(), default='', comment="复盘结论")
    num = db.Column(db.Integer(), default=0, comment="序号")
