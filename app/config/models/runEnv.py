# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class RunEnv(BaseModel):
    """ 运行环境表 """
    __tablename__ = "config_run_env"

    name = db.Column(db.String(255), nullable=True, comment="环境名字")
    num = db.Column(db.Integer(), nullable=True, comment="环境序号")
    addr = db.Column(db.String(255), nullable=True, comment="环境地址")
    code = db.Column(db.String(255), nullable=True, comment="环境code")
    test_type = db.Column(db.String(128), nullable=True, comment="环境所属测试类型，api:接口测试，web-ui：web-ui测试")
    desc = db.Column(db.String(255), nullable=True, comment="备注")

    @classmethod
    def get_id_list(cls, test_type=None):
        return [env.id for env in cls.get_all() if test_type is None or env.test_type == test_type]

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
        if form.test_type.data:
            filters.append(cls.test_type == form.test_type.data)
        if form.name.data:
            filters.append(cls.name.like(f'%{form.name.data}%'))
        if form.code.data:
            filters.append(cls.code.like(f'%{form.code.data}%'))
        if form.addr.data:
            filters.append(cls.addr.like(f'%{form.addr.data}%'))
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
