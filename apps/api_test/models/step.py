# -*- coding: utf-8 -*-
from sqlalchemy import Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseStep, HeadersFiled, ParamsFiled, DataFormFiled, DataUrlencodedFiled, DataJsonFiled, \
    ExtractsFiled, ValidatesFiled, BodyTypeFiled


class ApiStep(
    BaseStep, HeadersFiled, ParamsFiled, DataFormFiled, DataUrlencodedFiled, DataJsonFiled, ExtractsFiled,
    ValidatesFiled, BodyTypeFiled
):
    """ 测试步骤表 """
    __abstract__ = False
    __tablename__ = "api_test_step"
    __table_args__ = {"comment": "接口测试用例步骤表"}

    time_out: Mapped[int] = mapped_column(Integer(), default=60, nullable=True, comment="request超时时间，默认60秒")
    replace_host: Mapped[int] = mapped_column(
        Integer(), default=0,
        comment="是否使用用例所在项目的域名，1使用用例所在服务的域名，0使用步骤对应接口所在服务的域名")
    data_text: Mapped[str] = mapped_column(Text(), nullable=True, default=None, comment="文本参数")
    pop_header_filed: Mapped[list] = mapped_column(JSON, default=[], comment="头部参数中去除指定字段")
    api_id: Mapped[int] = mapped_column(Integer(), nullable=True, comment="步骤所引用的接口的id")
