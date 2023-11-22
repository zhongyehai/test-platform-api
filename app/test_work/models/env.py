# -*- coding: utf-8 -*-
from flask import g

from app.base_model import BaseModel, db


class Env(BaseModel):
    """ 测试环境资源表 """
    __tablename__ = "test_work_env"
    __table_args__ = {"comment": "环境、资源表"}

    business = db.Column(db.Integer(), comment="业务线")
    name = db.Column(db.String(255), comment="资源名")
    num = db.Column(db.Integer(), comment="序号")
    source_type = db.Column(db.String(255), comment="资源类型，账号:account、地址:addr")
    value = db.Column(db.String(255), comment="数据值")
    password = db.Column(db.String(255), default='', comment="登录密码")
    desc = db.Column(db.Text(), default='', comment="备注")
    parent = db.Column(db.Integer(), comment="当source_type为账号时，所属资源id")
