# -*- coding: utf-8 -*-
from flask import Flask

from utils.view import restful
from utils.log import logger
from config import ProductionConfig
from app.baseModel import db
from app.hooks.afterHook import register_after_hook
from app.hooks.beforeHook import register_before_hook
from app.hooks.errorhandler import register_errorhandler_hook

def create_app():
    app = Flask(__name__)
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
    from app.api_test.blueprint import api_test
    from app.web_ui_test.blueprint import web_ui_test
    from app.app_ui_test.blueprint import app_ui_test
    from app.assist.blueprint import assist
    from app.test_work.blueprint import test_work
    from app.config.blueprint import config_blueprint
    from app.tools.blueprint import tool
    from app.home.blueprint import home
    from app.system.blueprint import system_manage
    app.register_blueprint(api_test, url_prefix="/api/apiTest")
    app.register_blueprint(web_ui_test, url_prefix="/api/webUiTest")
    app.register_blueprint(app_ui_test, url_prefix="/api/appUiTest")
    app.register_blueprint(assist, url_prefix="/api/assist")
    app.register_blueprint(config_blueprint, url_prefix="/api/config")
    app.register_blueprint(test_work, url_prefix="/api/testWork")
    app.register_blueprint(tool, url_prefix="/api/tools")
    app.register_blueprint(home, url_prefix="/api/home")
    app.register_blueprint(system_manage, url_prefix="/api/system")

    return app
