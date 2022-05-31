#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : __init__.py
# @Software: PyCharm
import os

from flask import Flask
from flask_login import LoginManager

from app.utils import globalVariable
from app.utils.log import logger
from config.config import conf, ProductionConfig  # ,logger
from app.baseModel import db

login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.conf = conf
    app.config.from_object(ProductionConfig)
    app.logger = logger
    ProductionConfig.init_app(app)

    db.init_app(app)
    db.app = app
    db.create_all()
    login_manager.init_app(app)

    from app.api_test import api_test as api_test_blueprint
    from app.ui_test import ui_test as ui_test_blueprint
    from app.ucenter import ucenter as ucenter_blueprint
    from app.test_work import test_work as test_work_blueprint
    from app.config import config as config_blueprint
    from app.tools import tool as tool_blueprint
    app.register_blueprint(api_test_blueprint, url_prefix='/api/apiTest')
    app.register_blueprint(ui_test_blueprint, url_prefix='/api/uiTest')
    app.register_blueprint(ucenter_blueprint, url_prefix='/api/ucenter')
    app.register_blueprint(config_blueprint, url_prefix='/api/config')
    app.register_blueprint(test_work_blueprint, url_prefix='/api/testWork')
    app.register_blueprint(tool_blueprint, url_prefix='/api/tool')

    return app
