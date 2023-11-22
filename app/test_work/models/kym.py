# -*- coding: utf-8 -*-
from app.base_model import BaseModel, db


class KYMModule(BaseModel):
    """ KYM分析表 """
    __tablename__ = "test_work_kym"
    __table_args__ = {"comment": "KYM分析表"}

    project = db.Column(db.String(255), comment="服务名")
    kym = db.Column(db.JSON, default={}, comment="kym分析")
