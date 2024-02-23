# -*- coding: utf-8 -*-
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class KYMModule(BaseModel):
    """ KYM分析表 """
    __tablename__ = "test_work_kym"
    __table_args__ = {"comment": "KYM分析表"}

    project: Mapped[str] = mapped_column(String(255), nullable=False, comment="服务名")
    kym: Mapped[dict] = mapped_column(JSON, default={}, comment="kym分析")
