# -*- coding: utf-8 -*-

from app.baseModel import BaseStep, db


class UiStep(BaseStep):
    """ 测试步骤表 """
    __abstract__ = False

    __tablename__ = 'ui_test_step'

    wait_time_out = db.Column(db.Integer(), default=10, nullable=True, comment='等待元素出现的时间，默认10秒')
    execute_type = db.Column(db.String(255), comment='执行方式')
    send_keys = db.Column(db.String(255), comment='要输入的文本内容')
    extracts = db.Column(
        db.Text(),
        default='[{"key": null, "extract_type": null, "value": null, "remark": null}]',
        comment='提取信息'
    )
    validates = db.Column(
        db.Text(),
        default='[{"element": null, "key": null, "validate_type": null, "data_type": null, "value": null, "remark": null}]',
        comment='断言信息')

    project_id = db.Column(db.Integer, db.ForeignKey('ui_test_project.id'), comment='步骤所在的服务的id')
    project = db.relationship('UiProject', backref='steps')

    case_id = db.Column(db.Integer, db.ForeignKey('ui_test_case.id'), comment='步骤所在的用例的id')

    page_id = db.Column(db.Integer, db.ForeignKey('ui_test_page.id'), comment='步骤所在的元素对应的页面的id')
    page = db.relationship('UiPage', backref='steps')

    element_id = db.Column(db.Integer, db.ForeignKey('ui_test_element.id'), comment='步骤所引用的元素的id')
    element = db.relationship('UiElement', backref='steps')
