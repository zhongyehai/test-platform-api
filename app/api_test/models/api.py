# -*- coding: utf-8 -*-
from app.baseModel import BaseApi, db


class ApiMsg(BaseApi):
    """ 接口表 """
    __abstract__ = False

    __tablename__ = 'api_test_api'

    addr = db.Column(db.String(255), nullable=True, comment='地址')
    up_func = db.Column(db.Text(), default='', comment='接口执行前的函数')
    down_func = db.Column(db.Text(), default='', comment='接口执行后的函数')
    method = db.Column(db.String(10), nullable=True, comment='请求方式')
    headers = db.Column(db.Text(), default='[{"key": null, "remark": null, "value": null}]', comment='头部信息')
    params = db.Column(db.Text(), default='[{"key": null, "value": null}]', comment='url参数')
    data_type = db.Column(db.String(10), nullable=True, default='json', comment='参数类型，json、form-data、xml')
    data_form = db.Column(db.Text(),
                          default='[{"data_type": null, "key": null, "remark": null, "value": null}]',
                          comment='form-data参数')
    data_json = db.Column(db.Text(), default='{}', comment='json参数')
    data_xml = db.Column(db.Text(), default='', comment='xml参数')
    extracts = db.Column(
        db.Text(),
        default='[{"key": null, "data_source": null, "value": null, "remark": null}]',
        comment='提取信息'
    )
    validates = db.Column(
        db.Text(),
        default='[{"data_source": null, "key": null, "validate_type": null, "data_type": null, "value": null, "remark": null}]',
        comment='断言信息')

    project_id = db.Column(db.Integer(), nullable=True, comment='所属的服务id')
    yapi_id = db.Column(db.Integer(), comment='当前接口在yapi平台的id')

    module_id = db.Column(db.Integer(), db.ForeignKey('api_test_module.id'), comment='所属的接口模块id')
    module = db.relationship('ApiModule', backref='apis')


    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(ApiMsg.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(ApiMsg.name.like(f'%{form.name.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=ApiMsg.num.asc()
        )
