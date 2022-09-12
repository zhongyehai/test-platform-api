# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restx import Api

system_manage_blueprint = Blueprint('system', __name__)
system_manage = Api(
    system_manage_blueprint,
    version="1.0",
    doc="/swagger",
    title="系统管理",
    description="系统管理相关接口"
)

from .views import errorRecord, role, user
