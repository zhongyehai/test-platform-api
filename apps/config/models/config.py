# -*- coding: utf-8 -*-
from sqlalchemy import Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import NumFiled


class ConfigType(NumFiled):
    """ 配置类型表 """

    __tablename__ = "config_type"
    __table_args__ = {"comment": "配置类型表"}

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, comment="字段名")
    desc: Mapped[str] = mapped_column(Text(), nullable=True, comment="描述")


class Config(NumFiled):
    """ 配置表 """

    __tablename__ = "config_config"
    __table_args__ = {"comment": "配置表"}

    type: Mapped[int] = mapped_column(Integer(), nullable=False, index=True, comment="配置类型")
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, unique=True, comment="配置名")
    value: Mapped[str] = mapped_column(Text(), comment="配置值")
    desc: Mapped[str] = mapped_column(Text(), nullable=True, comment="描述")

    @classmethod
    def get_config_value(cls, config_name):
        return cls.db.session.query(cls.value).filter(cls.name == config_name).first()[0]  # ('60',)

    @classmethod
    def get_pip_command(cls):
        """ 获取pip_command配置项 """
        return cls.get_config_value("pip_command")

    @classmethod
    def get_kym(cls):
        """ 获取kym配置项 """
        return cls.loads(cls.get_config_value("kym"))

    @classmethod
    def get_callback_webhook(cls):
        return cls.get_config_value("callback_webhook")

    @classmethod
    def get_call_back_response(cls):
        return cls.get_config_value("call_back_response")

    @classmethod
    def get_data_source_callback_addr(cls):
        return cls.get_config_value("data_source_callback_addr")

    @classmethod
    def get_data_source_callback_token(cls):
        return cls.get_config_value("data_source_callback_token")

    @classmethod
    def get_run_time_error_message_send_addr(cls):
        return cls.get_config_value("run_time_error_message_send_addr")

    @classmethod
    def get_request_time_out(cls):
        return cls.get_config_value("request_time_out")

    @classmethod
    def get_pause_step_time_out(cls):
        return int(cls.get_config_value("pause_step_time_out"))

    @classmethod
    def get_response_time_level(cls):
        return cls.loads(cls.get_config_value("response_time_level"))

    @classmethod
    def get_wait_time_out(cls):
        return cls.get_config_value("wait_time_out")

    @classmethod
    def get_report_host(cls):
        return cls.get_config_value("report_host")

    @classmethod
    def get_func_error_addr(cls):
        return cls.get_config_value("func_error_addr")

    @classmethod
    def get_diff_api_addr(cls):
        return cls.get_config_value("diff_api_addr")

    @classmethod
    def get_api_report_addr(cls):
        return cls.get_config_value("api_report_addr")

    @classmethod
    def get_web_ui_report_addr(cls):
        return cls.get_config_value("web_ui_report_addr")

    @classmethod
    def get_app_ui_report_addr(cls):
        return cls.get_config_value("app_ui_report_addr")

    @classmethod
    def get_appium_new_command_timeout(cls):
        return cls.get_config_value("appium_new_command_timeout")

    @classmethod
    def get_ui_report_addr(cls):
        return cls.get_config_value("ui_report_addr")

    @classmethod
    def get_sync_mock_data(cls):
        return cls.loads(cls.get_config_value("sync_mock_data"))

    @classmethod
    def get_save_func_permissions(cls):
        return cls.get_config_value("save_func_permissions")

    @classmethod
    def get_call_back_msg_addr(cls):
        return cls.get_config_value("call_back_msg_addr")

    @classmethod
    def get_shell_command_info(cls):
        """ 获取sell造数据的配置项 """
        return cls.loads(cls.get_config_value("shell_command_info"))
