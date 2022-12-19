# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class KYMModule(BaseModel):
    """ KYM分析表 """
    __tablename__ = "test_work_kym"

    project = db.Column(db.String(255), comment="服务名")
    kym = db.Column(db.Text, default="{}", comment="kym分析")
