# -*- coding: utf-8 -*-
from flask import g
from app.baseModel import BaseModel, db
from app.system.models.user import User


class BusinessLine(BaseModel):
    """ 业务线 """

    __tablename__ = "config_business"
    __table_args__ = {"comment": "业务线配置表"}
    name = db.Column(db.String(128), nullable=True, comment="业务线名")
    code = db.Column(db.String(128), nullable=True, unique=True, comment="业务线编码")
    receive_type = db.Column(db.String(16), default="0",
                             comment="接收通知类型：0:不接收、we_chat:企业微信、ding_ding:钉钉")
    webhook_list = db.Column(db.Text(), default='[]', comment="接收该业务线自动化测试阶段统计通知地址")
    env_list = db.Column(db.Text(), default='[]', comment="业务线能使用的运行环境")
    num = db.Column(db.Integer(), nullable=True, comment="序号")
    desc = db.Column(db.Text(), comment="描述")

    @classmethod
    def get_env_list(cls, business_id):
        """ 根据业务线获取选择的运行环境 """
        return cls.loads(cls.get_first(id=business_id).env_list)

    @classmethod
    def business_to_user(cls, business_id_list, user_id_list, command):
        """ 管理业务线与用户的 绑定/解绑  command: add、delete """
        user_list = User.query.filter(User.id.in_(user_id_list)).all()
        for user in user_list:
            user_business = cls.loads(user.business_list)
            if command == "add":  # 绑定
                user_business_id_list = list({*business_id_list, *user_business})
            else:  # 取消绑定
                user_business_id_list = list(set(user_business).difference(set(business_id_list)))
            user.update({"business_list": user_business_id_list})

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if not form.getAll.data and cls.is_not_admin():  # 如果用户不是管理员权限，则只返回当前用户的业务线
            filters.append(cls.id.in_(g.business_list))
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.code.data:
            filters.append(cls.code.like(f'%{form.code.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.id.desc()
        )
