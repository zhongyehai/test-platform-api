# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restx import Api

assist_blueprint = Blueprint('Assist', __name__)
assist = Api(
    assist_blueprint,
    version="1.0",
    doc="/swagger",
    title="自动化测试辅助管理",
    description="自动化测试辅助管理相关接口"
)
from .views import dataPool, errorRecord, file, func, swagger, yapi
