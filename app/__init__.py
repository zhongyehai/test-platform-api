# -*- coding: utf-8 -*-

import os

from flask import Flask

from utils.view import restful
from utils.log import logger
from config.config import conf, ProductionConfig
from app.baseModel import db
from app.hooks.afterHook import register_after_hook
from app.hooks.beforeHook import register_before_hook
from app.hooks.errorhandler import register_errorhandler_hook

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.conf = conf
    app.config.from_object(ProductionConfig)
    app.logger = logger
    app.db = db
    app.restful = restful  # 方便视图返回restful风格，不用每个视图都导包

    # 注册数据库
    db.init_app(app)
    db.app = app
    db.create_all()

    # 注册钩子函数
    register_before_hook(app)  # 注册前置钩子函数
    register_after_hook(app)  # 注册后置钩子函数
    register_errorhandler_hook(app)  # 注册异常捕获钩子函数

    # 注册蓝图
    from app.api_test import api_test_blueprint
    from app.web_ui_test import web_ui_test_blueprint
    from app.assist import assist_blueprint
    from app.test_work import test_work_blueprint
    from app.config import config_blueprint
    from app.tools import tool_blueprint
    from app.home import home_blueprint
    from app.system import system_manage_blueprint
    app.register_blueprint(api_test_blueprint, url_prefix='/api/apiTest')
    app.register_blueprint(web_ui_test_blueprint, url_prefix='/api/webUiTest')
    app.register_blueprint(assist_blueprint, url_prefix='/api/assist')
    app.register_blueprint(config_blueprint, url_prefix='/api/config')
    app.register_blueprint(test_work_blueprint, url_prefix='/api/testWork')
    app.register_blueprint(tool_blueprint, url_prefix='/api/tools')
    app.register_blueprint(home_blueprint, url_prefix='/api/home')
    app.register_blueprint(system_manage_blueprint, url_prefix='/api/system')

    return app
