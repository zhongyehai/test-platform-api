# -*- coding: utf-8 -*-
import time
import hmac
import hashlib
import base64
import urllib.parse

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ...base_model import NumFiled
from ...enums import WebHookTypeEnum


class WebHook(NumFiled):
    """ webhook管理 """
    __tablename__ = "config_webhook"
    __table_args__ = {"comment": "webhook管理表"}

    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="webhook名字")
    addr: Mapped[str] = mapped_column(String(255), nullable=False, comment="webhook地址")
    secret: Mapped[str] = mapped_column(String(255), nullable=True, comment="webhook秘钥")
    webhook_type: Mapped[WebHookTypeEnum] = mapped_column(
        String(255), nullable=False, comment="webhook类型，钉钉、企业微信、飞书")
    desc: Mapped[str] = mapped_column(String(255), nullable=True, comment="备注")

    @classmethod
    def get_webhook_list(cls, webhook_type: WebHookTypeEnum, webhook_list: list):
        query_list = cls.db.session.query(
            cls.addr, cls.secret).filter(cls.webhook_type == webhook_type, cls.id.in_(webhook_list)).all()
        return [cls.build_webhook_addr(webhook_type, data[0], data[1]) for data in query_list]

    @classmethod
    def build_webhook_addr(cls, webhook_type: str, addr: str, secret: str):
        """ 解析webhook地址 """
        if secret:
            if webhook_type == WebHookTypeEnum.ding_ding.value:
                return cls.build_ding_ding_addr(addr, secret)
        return addr

    @classmethod
    def build_ding_ding_addr(cls, addr: str, secret: str):
        """ 钉钉加签 """
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f'{addr}&timestamp={timestamp}&sign={sign}'
