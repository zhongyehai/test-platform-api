# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class ConfigType(BaseModel):
    """ 配置类型表 """

    __tablename__ = 'config_type'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='字段名')
    desc = db.Column(db.Text(), comment='描述')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )


class Config(BaseModel):
    """ 配置表 """

    __tablename__ = 'config'

    name = db.Column(db.String(128), nullable=True, unique=True, comment='字段名')
    value = db.Column(db.Text(), nullable=True, comment='字段值')
    type = db.Column(db.Integer(), nullable=True, comment='配置类型')
    desc = db.Column(db.Text(), comment='描述')

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.type.data:
            filters.append(cls.type == form.type.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.asc()
        )

    @classmethod
    def get_kym(cls):
        """ 获取kym配置项 """
        return cls.loads(cls.get_first(name='kym').value)

    @classmethod
    def get_run_test_env(cls):
        """ 获取运行环境配置项 """
        return cls.loads(cls.get_first(name='run_test_env').value)

    @classmethod
    def get_http_methods(cls):
        """ 配置的http请求方法 """
        return cls.get_first(name='http_methods').value

    @classmethod
    def get_default_diff_message_send_addr(cls):
        """ 配置的对比结果通知地址 """
        return cls.get_first(name='default_diff_message_send_addr').value

    @classmethod
    def get_make_user_info_mapping(cls):
        return cls.get_first(name='make_user_info_mapping').value

    @classmethod
    def get_callback_webhook(cls):
        return cls.get_first(name='callback_webhook').value

    @classmethod
    def get_call_back_response(cls):
        return cls.get_first(name='call_back_response').value

    @classmethod
    def get_data_source_callback_addr(cls):
        return cls.get_first(name='data_source_callback_addr').value

    @classmethod
    def get_data_source_callback_token(cls):
        return cls.get_first(name='data_source_callback_token').value

    @classmethod
    def get_run_time_error_message_send_addr(cls):
        return cls.get_first(name='run_time_error_message_send_addr').value

    @classmethod
    def get_request_time_out(cls):
        return cls.get_first(name='request_time_out').value

    @classmethod
    def get_wait_time_out(cls):
        return cls.get_first(name='wait_time_out').value

    @classmethod
    def get_func_error_addr(cls):
        return cls.get_first(name='func_error_addr').value

    @classmethod
    def get_diff_api_addr(cls):
        return cls.get_first(name='diff_api_addr').value

    @classmethod
    def get_api_report_addr(cls):
        return cls.get_first(name='api_report_addr').value

    @classmethod
    def get_ui_report_addr(cls):
        return cls.get_first(name='ui_report_addr').value
