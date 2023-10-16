# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class AutoTestUser(BaseModel):
    """ 自动化测试用户表 """
    __tablename__ = "auto_test_user"
    __table_args__ = {"comment": "自动化测试用户数据池"}

    mobile = db.Column(db.String(128), nullable=True, index=True, default="", comment="手机号")
    company_name = db.Column(db.String(128), nullable=True, default="", comment="公司名")
    access_token = db.Column(db.Text, nullable=True, default="", comment="access_token")
    refresh_token = db.Column(db.Text, nullable=True, default="", comment="refresh_token")
    user_id = db.Column(db.String(128), nullable=True, default="", comment="用户id")
    company_id = db.Column(db.String(128), nullable=True, default="", comment="公司id")
    password = db.Column(db.String(128), nullable=True, default="", comment="密码")
    role = db.Column(db.String(128), nullable=True, default="", comment="角色")
    comment = db.Column(db.Text, nullable=True, default="", comment="备注")
    env = db.Column(db.String(64), nullable=True, index=True, default="", comment="数据对应的环境")


class DataPool(BaseModel):
    """ 数据池 """
    __tablename__ = "auto_test_data_pool"
    __table_args__ = {"comment": "测试数据池"}

    env = db.Column(db.String(10), nullable=True, index=True, default="", comment="数据对应的环境")
    mobile = db.Column(db.String(32), nullable=True, index=True, default="", comment="手机号")
    password = db.Column(db.String(32), nullable=True, default="", comment="密码")
    business_order_no = db.Column(db.String(64), nullable=True, default="", comment="业务流水号")
    amount = db.Column(db.String(64), nullable=True, default="", comment="金额")
    business_status = db.Column(db.String(64), nullable=True, default="", comment="业务状态，自定义")
    use_status = db.Column(
        db.String(64), nullable=True, default="", comment="使用状态，未使用：not_used、使用中：in_use、已使用：used"
    )
    desc = db.Column(db.String(255), nullable=True, default="", comment="备注")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.env.data:
            filters.append(cls.env == form.env.data)
        if form.mobile.data:
            filters.append(cls.mobile.like(f'%{form.mobile.data}%'))
        if form.business_order_no.data:
            filters.append(cls.business_order_no.like(f'%{form.business_order_no.data}%'))
        if form.business_status.data:
            filters.append(cls.business_status == form.business_status.data)
        if form.use_status.data:
            filters.append(cls.use_status == form.use_status.data)

        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.created_time.asc()
        )
