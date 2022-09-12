# -*- coding: utf-8 -*-
from flask import Blueprint
from flask_restx import Api

home_blueprint = Blueprint('home', __name__)
home = Api(
    home_blueprint,
    version="1.0",
    doc="/swagger",
    title="首页",
    description="首页相关接口"
)


from .views import apiTest
