# -*- coding: utf-8 -*-
from app.baseModel import BaseApi, db


class ApiMsg(BaseApi):
    """ 接口表 """
    __abstract__ = False

    __tablename__ = "api_test_api"

    time_out = db.Column(db.Integer(), default=60, nullable=True, comment="request超时时间，默认60秒")
    addr = db.Column(db.String(255), nullable=True, comment="地址")
    up_func = db.Column(db.Text(), default="", comment="接口执行前的函数")
    down_func = db.Column(db.Text(), default="", comment="接口执行后的函数")
    method = db.Column(db.String(10), nullable=True, comment="请求方式")
    level = db.Column(db.String(10), nullable=True, default="P1", comment="接口重要程度：P0、P1、P2")
    headers = db.Column(db.Text(), default='[{"key": null, "value": null, "remark": null}]', comment="头部信息")
    params = db.Column(db.Text(), default='[{"key": null, "value": null, "remark": null}]', comment="url参数")
    data_type = db.Column(db.String(10), nullable=True, default="json", comment="参数类型，json、form-data、xml")
    data_form = db.Column(db.Text(),
                          default='[{"data_type": null, "key": null, "remark": null, "value": null}]',
                          comment="form-data参数")
    data_urlencoded = db.Column(db.Text(), default="{}", comment="form_urlencoded参数")
    data_json = db.Column(db.Text(), default="{}", comment="json参数")
    data_text = db.Column(db.Text(), default="", comment="文本参数")
    response = db.Column(db.Text(), default="{}", comment="响应对象")
    extracts = db.Column(
        db.Text(),
        default='[{"key": null, "data_source": null, "value": null, "remark": null, "update_to_header": null}]',
        comment="提取信息"
    )
    validates = db.Column(
        db.Text(),
        default='[{"data_source": null, "key": null, "validate_type": null, "data_type": null, "value": null, "remark": null}]',
        comment="断言信息")
    deprecated = db.Column(db.Boolean(), default=False, comment="是否废弃")
    quote_count = db.Column(db.Integer(), nullable=True, default=0, comment="被引用次数，即多少个步骤直接使用了此接口")
    yapi_id = db.Column(db.Integer(), comment="当前接口在yapi平台的id")

    def add_quote_count(self):
        """ 被引用次数+1 """
        with db.auto_commit():
            self.quote_count = 1 if self.quote_count is None else self.quote_count + 1

    def subtract_quote_count(self):
        """ 被引用次数-1 """
        with db.auto_commit():
            self.quote_count = 0 if self.quote_count is None else self.quote_count - 1

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.moduleId.data:
            filters.append(ApiMsg.module_id == form.moduleId.data)
        if form.name.data:
            filters.append(ApiMsg.name.like(f"%{form.name.data}%"))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=ApiMsg.num.asc()
        )
