# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class RunEnv(BaseModel):
    """ 运行环境表 """
    __tablename__ = "config_run_env"
    __table_args__ = {"comment": "运行环境配置表"}

    name = db.Column(db.String(255), nullable=True, comment="环境名字")
    num = db.Column(db.Integer(), nullable=True, comment="环境序号")
    code = db.Column(db.String(255), nullable=True, comment="环境code")
    desc = db.Column(db.String(255), nullable=True, comment="备注")
    group = db.Column(db.String(255), nullable=True, comment="环境分组")

    @classmethod
    def get_id_list(cls):
        return [env.id for env in cls.get_all()]

    @classmethod
    def get_data_byid_or_code(cls, id_or_code):
        """ 根据id或者code获取数据 """
        return cls.get_first(id=id_or_code) or cls.get_first(code=id_or_code)

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.create_user.data:
            filters.append(cls.create_user == form.create_user.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.code.data:
            filters.append(cls.code.like(f'%{form.code.data}%'))
        if form.group.data:
            filters.append(cls.group.like(f'%{form.group.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
