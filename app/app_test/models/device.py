# -*- coding: utf-8 -*-
from app.base_model import BaseModel, db


class AppUiRunServer(BaseModel):
    """ 运行服务器表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_run_server"
    __table_args__ = {"comment": "APP测试运行服务器表"}

    name = db.Column(db.String(255), nullable=True, unique=True, comment="服务器名字")
    num = db.Column(db.Integer(), comment="序号")
    os = db.Column(db.String(255), nullable=True, comment="服务器系统类型：windows/mac/linux")
    ip = db.Column(db.String(255), nullable=True, comment="服务器ip地址")
    port = db.Column(db.String(255), default="4723", nullable=True, comment="服务器端口号")
    status = db.Column(db.Integer(), default=0, comment="最近一次访问状态，0:未访问，1:访问失败，2:访问成功")

    def request_fail(self):
        self.model_update({"status": 1})

    def request_success(self):
        self.model_update({"status": 2})


class AppUiRunPhone(BaseModel):
    """ 运行终端手机表 """
    __abstract__ = False
    __tablename__ = "app_ui_test_run_phone"
    __table_args__ = {"comment": "APP测试运行手机表"}

    name = db.Column(db.String(255), nullable=True, unique=True, comment="设备名字")
    num = db.Column(db.Integer(), comment="序号")
    os = db.Column(db.String(255), nullable=True, comment="设备系统类型：Android/ios")
    os_version = db.Column(db.String(255), nullable=True, comment="设备系统版本号")
    device_id = db.Column(db.String(255), nullable=True, comment="终端设备id")
    extends = db.Column(db.JSON, default={}, comment="设备扩展字段")
    screen = db.Column(db.String(64), nullable=True, comment="屏幕分辨率")
