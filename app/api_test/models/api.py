# -*- coding: utf-8 -*-
from app.base_model import BaseApi, db, UpFuncFiled, DownFuncFiled, HeadersFiled, ParamsFiled, DataFormFiled, \
    DataUrlencodedFiled, DataJsonFiled, ExtractsFiled, ValidatesFiled, BodyTypeFiled, StatusFiled
from app.enums import ApiMethodEnum, ApiLevelEnum


class ApiMsg(
    BaseApi, UpFuncFiled, DownFuncFiled, HeadersFiled, ParamsFiled, DataFormFiled, DataUrlencodedFiled, DataJsonFiled,
    ExtractsFiled, ValidatesFiled, BodyTypeFiled, StatusFiled
):
    """ 接口表 """
    __abstract__ = False
    __tablename__ = "api_test_api"
    __table_args__ = {"comment": "接口测试接口信息表"}

    time_out = db.Column(db.Integer(), default=60, nullable=True, comment="request超时时间，默认60秒")
    addr = db.Column(db.String(255), nullable=True, comment="地址")
    method = db.Column(db.Enum(*ApiMethodEnum.get_value_tuple()), default=ApiMethodEnum.GET, comment="请求方式")
    level = db.Column(
        db.Enum(*ApiLevelEnum.get_value_tuple()), default=ApiLevelEnum.P1, comment="接口重要程度：P0、P1、P2")
    data_text = db.Column(db.Text(), default="", comment="文本参数")
    response = db.Column(db.JSON, default={}, comment="响应对象")
    use_count = db.Column(db.Integer(), nullable=True, default=0, comment="被使用次数，即多少个步骤直接使用了此接口")
