# -*- coding: utf-8 -*-
from sqlalchemy import or_
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...base_model import NumFiled
from ..model_factory import BusinessLine


class RunEnv(NumFiled):
    """ 运行环境表 """
    __tablename__ = "config_run_env"
    __table_args__ = {"comment": "运行环境配置表"}

    name: Mapped[str] = mapped_column(String(255), nullable=True, comment="环境名字")
    code: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, comment="环境code")
    desc: Mapped[str] = mapped_column(String(255), nullable=True, comment="备注")
    group: Mapped[str] = mapped_column(String(255), nullable=True, comment="环境分组")

    @classmethod
    def get_data_by_id_or_code(cls, id_or_code):
        """ 根据id或者code获取数据 """
        return cls.query.filter(or_(cls.id == id_or_code, cls.code == id_or_code)).first()

    @classmethod
    def env_to_business(cls, env_id_list, business_id_list, command):
        """ 管理环境与业务线的 绑定/解绑  command: add、delete """
        business_query_list = BusinessLine.db.session.query(
            BusinessLine.id, BusinessLine.env_list).filter(BusinessLine.id.in_(business_id_list)).all()
        for business_query in business_query_list:
            business_env = business_query[1]
            if command == "add":  # 绑定
                business_env_list = list({*env_id_list, *business_env})
            else:  # 取消绑定
                business_env_list = list(set(business_env).difference(set(env_id_list)))
            BusinessLine.query.filter_by(id=business_query[0]).update({"env_list": business_env_list})
