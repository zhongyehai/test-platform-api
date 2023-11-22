# -*- coding: utf-8 -*-
from app.base_model import BaseStep, db, ExtractsFiled, ValidatesFiled


class AppUiStep(BaseStep, ExtractsFiled, ValidatesFiled):
    """ 测试步骤表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_step"
    __table_args__ = {"comment": "APP测试步骤表"}

    wait_time_out = db.Column(db.Integer(), default=10, nullable=True, comment="等待元素出现的时间，默认10秒")
    execute_type = db.Column(db.String(255), comment="执行方式")
    send_keys = db.Column(db.String(255), comment="要输入的文本内容")
    element_id = db.Column(db.Integer(), comment="步骤所引用的元素的id")
