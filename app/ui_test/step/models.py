#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/4/16 9:42
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class UiStep(BaseModel):
    """ 测试步骤表 """
    __tablename__ = 'ui_test_step'
    num = db.Column(db.Integer(), nullable=True, comment='步骤序号，执行顺序按序号来')
    is_run = db.Column(db.Boolean(), default=True, comment='是否执行此步骤，True执行，False不执行，默认执行')
    run_times = db.Column(db.Integer(), default=1, comment='执行次数，默认执行1次')

    name = db.Column(db.String(255), comment='步骤名称')
    execute_type = db.Column(db.String(255), comment='执行方式')
    send_keys = db.Column(db.String(255), comment='要输入的文本内容')
    up_func = db.Column(db.Text(), default='', comment='步骤执行前的函数')
    down_func = db.Column(db.Text(), default='', comment='步骤执行后的函数')
    extracts = db.Column(
        db.Text(),
        default='[{"key": null, "extract_type": null, "value": null, "remark": null}]',
        comment='提取信息'
    )
    validates = db.Column(
        db.Text(),
        default='[{"element": null, "key": null, "validate_type": null, "data_type": null, "value": null, "remark": null}]',
        comment='断言信息')
    data_driver = db.Column(db.Text(), default='[]', comment='数据驱动，若此字段有值，则走数据驱动的解析')
    quote_case = db.Column(db.String(5), default='', comment='引用用例的id')

    project_id = db.Column(db.Integer, db.ForeignKey('ui_test_project.id'), comment='步骤所在的服务的id')
    project = db.relationship('UiProject', backref='steps')

    case_id = db.Column(db.Integer, db.ForeignKey('ui_test_case.id'), comment='步骤所在的用例的id')

    page_id = db.Column(db.Integer, db.ForeignKey('ui_test_page.id'), comment='步骤所在的元素对应的页面的id')
    page = db.relationship('UiPage', backref='steps')

    element_id = db.Column(db.Integer, db.ForeignKey('ui_test_element.id'), comment='步骤所引用的元素的id')
    element = db.relationship('UiElement', backref='steps')

    def to_dict(self, *args, **kwargs):
        return super(UiStep, self).to_dict(
            to_dict=["headers", "params", "data_form", "data_json", "extracts", "validates", "data_driver"]
        )
