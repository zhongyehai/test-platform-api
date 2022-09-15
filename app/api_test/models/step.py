# -*- coding: utf-8 -*-
from app.api_test.models.api import ApiMsg
from app.baseModel import BaseStep, db


class ApiStep(BaseStep):
    """ 测试步骤表 """
    __abstract__ = False

    __tablename__ = 'api_test_step'

    time_out = db.Column(db.Integer(), default=60, nullable=True, comment='request超时时间，默认60秒')
    replace_host = db.Column(db.Boolean(), default=False, comment='是否使用用例所在项目的域名，True使用用例所在服务的域名，False使用步骤对应接口所在服务的域名')
    headers = db.Column(db.Text(), default='[{"key": null, "remark": null, "value": null}]', comment='头部信息')
    params = db.Column(db.Text(), default='[{"key": null, "value": null}]', comment='url参数')
    data_form = db.Column(db.Text(),
                          default='[{"data_type": null, "key": null, "remark": null, "value": null}]',
                          comment='form-data参数')
    data_urlencoded = db.Column(db.Text(), default='{}', comment='form_urlencoded参数')
    data_json = db.Column(db.Text(), default='{}', comment='json参数')
    data_text = db.Column(db.Text(), default=None, comment='文本参数')
    data_type = db.Column(db.String(10), default='json', comment='请求体参数类型')
    extracts = db.Column(
        db.Text(),
        default='[{"key": null, "data_source": null, "value": null, "remark": null, "update_to_header": null}]',
        comment='提取信息'
    )
    validates = db.Column(
        db.Text(),
        default='[{"data_source": null, "key": null, "validate_type": null, "data_type": null, "value": null, "remark": null}]',
        comment='断言信息')

    project_id = db.Column(db.Integer, db.ForeignKey('api_test_project.id'), comment='步骤所在的服务的id')
    project = db.relationship('ApiProject', backref='steps')

    case_id = db.Column(db.Integer, db.ForeignKey('api_test_case.id'), comment='步骤所在的用例的id')

    api_id = db.Column(db.Integer, db.ForeignKey('api_test_api.id'), comment='步骤所引用的接口的id')
    api = db.relationship('ApiMsg', backref='apis')

    def add_api_quote_count(self, api=None):
        """ 步骤对应的接口被引用次数+1 """
        if not self.quote_case:
            if not api:
                api = ApiMsg.get_first(id=self.api_id)
            api.add_quote_count()

    def subtract_api_quote_count(self, api=None):
        """ 步骤对应的被引用次数-1 """
        if not self.quote_case:
            if not api:
                api = ApiMsg.get_first(id=self.api_id)
            api.subtract_quote_count()
