# -*- coding: utf-8 -*-
from sqlalchemy import JSON, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from ...base_model import NumFiled
from ...system.model_factory import User


class BusinessLine(NumFiled):
    """ 业务线 """

    __tablename__ = "config_business"
    __table_args__ = {"comment": "业务线配置表"}
    name: Mapped[str] = mapped_column(String(128), unique=True, comment="业务线名")
    code: Mapped[str] = mapped_column(String(128), unique=True, comment="业务线编码")
    receive_type: Mapped[str] = mapped_column(
        String(16), default="0", comment="接收通知类型：0:不接收、we_chat:企业微信、ding_ding:钉钉")
    webhook_list: Mapped[list] = mapped_column(JSON, default=[], comment="接收该业务线自动化测试阶段统计通知地址")
    env_list: Mapped[list] = mapped_column(JSON, default=[], comment="业务线能使用的运行环境")
    bind_env: Mapped[str] = mapped_column(
        String(8), default="human", comment="绑定环境机制，auto：新增环境时自动绑定，human：新增环境后手动绑定")
    desc: Mapped[str] = mapped_column(Text(), nullable=True, comment="描述")

    @classmethod
    def get_auto_bind_env_id_list(cls):
        """ 获取设置为自动绑定的业务线 """
        query_res = cls.query.filter(BusinessLine.bind_env == "auto").with_entities(BusinessLine.id).all()
        return cls.format_with_entities_query_list(query_res)

    @classmethod
    def get_env_list(cls, business_id):
        """ 根据业务线获取选择的运行环境 """
        env_list_query = cls.db.session.query(cls.env_list).filter(cls.id == business_id).first()
        return env_list_query[0]

    @classmethod
    def business_to_user(cls, business_id_list, user_id_list, command):
        """ 管理业务线与用户的 绑定/解绑  command: add、delete """
        user_query_list = User.db.session.query(User.id, User.business_list).filter(User.id.in_(user_id_list)).all()
        for user_query in user_query_list:
            user_business = user_query[1]
            if command == "add":  # 绑定
                user_business_id_list = list({*business_id_list, *user_business})
            else:  # 取消绑定
                user_business_id_list = list(set(user_business).difference(set(business_id_list)))
            User.query.filter_by(id=user_query[0]).update({"business_list": user_business_id_list})
