# -*- coding: utf-8 -*-
from sqlalchemy import Integer, String, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseApi, UpFuncFiled, DownFuncFiled, HeadersFiled, ParamsFiled, DataFormFiled, \
    DataUrlencodedFiled, DataJsonFiled, ExtractsFiled, ValidatesFiled, BodyTypeFiled, StatusFiled
from apps.enums import ApiMethodEnum, ApiLevelEnum


class ApiMsg(
    BaseApi, UpFuncFiled, DownFuncFiled, HeadersFiled, ParamsFiled, DataFormFiled, DataUrlencodedFiled, DataJsonFiled,
    ExtractsFiled, ValidatesFiled, BodyTypeFiled, StatusFiled
):
    """ 接口表 """
    __abstract__ = False
    __tablename__ = "api_test_api"
    __table_args__ = {"comment": "接口测试接口信息表"}

    time_out: Mapped[int] = mapped_column(Integer(), default=60, comment="request超时时间，默认60秒")
    addr: Mapped[str] = mapped_column(String(255), nullable=False, comment="接口地址")
    method: Mapped[ApiMethodEnum] = mapped_column(default=ApiMethodEnum.GET, comment="请求方式")
    level: Mapped[ApiLevelEnum] = mapped_column(default=ApiLevelEnum.P1, comment="接口重要程度：P0、P1、P2")
    data_text: Mapped[str] = mapped_column(Text(), nullable=True, default="", comment="文本参数")
    response: Mapped[dict] = mapped_column(JSON, default={}, comment="响应对象")
    use_count: Mapped[int] = mapped_column(Integer(), default=0, comment="被使用次数，即多少个步骤直接使用了此接口")
