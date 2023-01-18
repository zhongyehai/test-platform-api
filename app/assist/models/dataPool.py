# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class AutoTestUser(BaseModel):
    """ 自动化测试用户表 """
    __tablename__ = "auto_test_user"

    mobile = db.Column(db.String(128), nullable=True, default="", comment="手机号")
    company_name = db.Column(db.String(128), nullable=True, default="", comment="公司名")
    access_token = db.Column(db.Text, nullable=True, default="", comment="access_token")
    refresh_token = db.Column(db.Text, nullable=True, default="", comment="refresh_token")
    user_id = db.Column(db.String(128), nullable=True, default="", comment="用户id")
    company_id = db.Column(db.String(128), nullable=True, default="", comment="公司id")
    password = db.Column(db.String(128), nullable=True, default="", comment="密码")
    role = db.Column(db.String(128), nullable=True, default="", comment="角色")
    comment = db.Column(db.String(256), nullable=True, default="", comment="备注")
    env = db.Column(db.String(64), nullable=True, default="", comment="数据对应的环境")
