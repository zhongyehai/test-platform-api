# -*- coding: utf-8 -*-
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from apps.base_model import BaseElement


class AppUiElement(BaseElement):
    """ 页面元素表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_element"
    __table_args__ = {"comment": "APP测试元素表"}

    template_device: Mapped[int] = mapped_column(
        Integer(), comment="元素定位时参照的设备，定位方式为bounds时根据此设备参照分辨率")
