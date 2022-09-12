# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restx import Api

api_test_blueprint = Blueprint('apiTest', __name__)

api_test = Api(
    api_test_blueprint,
    version="1.0",
    doc="/swagger",
    title="接口自动化测试管理",
    description="接口自动化测试管理相关接口"
)

from .views import project, module, api, caseSet, case, step, task, report
