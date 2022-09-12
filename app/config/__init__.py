# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restx import Api

config_blueprint = Blueprint('config', __name__)
config = Api(
    config_blueprint,
    version="1.0",
    doc="/swagger",
    title="配置管理",
    description="配置管理相关接口"
)
from app.config.views import config, configType
