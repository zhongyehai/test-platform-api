# -*- coding: utf-8 -*-
from app.baseModel import BaseModel, db


class AppUiRunServer(BaseModel):
    """ 运行服务器表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_run_server"

    name = db.Column(db.String(255), nullable=True, comment="服务器名字")
    num = db.Column(db.Integer(), comment="序号")
    os = db.Column(db.String(255), nullable=True, comment="服务器系统类型：windows/mac/linux")
    ip = db.Column(db.String(255), nullable=True, comment="服务器ip地址")
    port = db.Column(db.String(255), default="4723", nullable=True, comment="服务器端口号")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        if form.os.data:
            filters.append(cls.os == form.os.data)
        if form.ip.data:
            filters.append(cls.ip == form.ip.data)
        if form.port.data:
            filters.append(cls.port == form.port.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )


class AppUiRunPhone(BaseModel):
    """ 运行终端手机表 """
    __abstract__ = False

    __tablename__ = "app_ui_test_run_phone"

    name = db.Column(db.String(255), nullable=True, comment="设备名字")
    num = db.Column(db.Integer(), comment="序号")
    os = db.Column(db.String(255), nullable=True, comment="设备系统类型：Android/ios")
    os_version = db.Column(db.String(255), nullable=True, comment="设备系统版本号")

    @classmethod
    def make_pagination(cls, form):
        """ 解析分页条件 """
        filters = []
        if form.name.data:
            filters.append(cls.name.like(f"%{form.name.data}%"))
        if form.os.data:
            filters.append(cls.os == form.os.data)
        if form.os_version.data:
            filters.append(cls.os_version == form.os_version.data)
        return cls.pagination(
            page_num=form.pageNum.data,
            page_size=form.pageSize.data,
            filters=filters,
            order_by=cls.num.asc()
        )
