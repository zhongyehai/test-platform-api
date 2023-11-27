# -*- coding: utf-8 -*-
from sqlalchemy import Text, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseModel


class AutoTestUser(BaseModel):
    """ 自动化测试用户表 """
    __tablename__ = "auto_test_user"
    __table_args__ = {"comment": "自动化测试用户数据池"}

    mobile: Mapped[str] = mapped_column(String(128), nullable=True, index=True, default="", comment="手机号")
    company_name: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="公司名")
    access_token: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="access_token")
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="refresh_token")
    user_id: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="用户id")
    company_id: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="公司id")
    password: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="密码")
    role: Mapped[str] = mapped_column(String(128), nullable=True, default="", comment="角色")
    comment: Mapped[str] = mapped_column(Text, nullable=True, default="", comment="备注")
    env: Mapped[str] = mapped_column(String(64), nullable=True, index=True, default="", comment="数据对应的环境")


class DataPool(BaseModel):
    """ 数据池 """
    __tablename__ = "auto_test_data_pool"
    __table_args__ = {"comment": "测试数据池"}

    env: Mapped[str] = mapped_column(String(10), nullable=True, index=True, default="", comment="数据对应的环境")
    mobile: Mapped[str] = mapped_column(String(32), nullable=True, index=True, default="", comment="手机号")
    password: Mapped[str] = mapped_column(String(32), nullable=True, default="", comment="密码")
    business_order_no: Mapped[str] = mapped_column(String(64), nullable=True, default="", comment="业务流水号")
    amount: Mapped[str] = mapped_column(String(64), nullable=True, default="", comment="金额")
    business_status: Mapped[str] = mapped_column(String(64), nullable=True, default="", comment="业务状态，自定义")
    use_status: Mapped[str] = mapped_column(
        String(64), nullable=True, default="", comment="使用状态，未使用：not_used、使用中：in_use、已使用：used")
    desc: Mapped[str] = mapped_column(String(255), nullable=True, default="", comment="备注")
