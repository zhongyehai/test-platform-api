# -*- coding: utf-8 -*-
from flask import Flask

from utils.util.json_util import CustomJSONEncoder
from utils.view import restful
# from utils.logs.log import logger
from config import _SystemConfig
from apps.base_model import db
from apps.hooks.after_request import register_after_hook
from apps.hooks.before_request import register_before_hook
from apps.hooks.error_handler import register_errorhandler_hook


def create_app():
    app = Flask(__name__)
    app.json_encoder = CustomJSONEncoder
    app.config.from_object(_SystemConfig)

    # 挂载日志
    # app.logger.handlers = logger.handlers
    # app.logger.setLevel(logger.level)

    app.db = db
    app.restful = restful  # 方便视图返回restful风格，不用每个视图都导包

    # 注册数据库
    db.init_app(app)
    db.app = app

    # 注册钩子函数
    register_before_hook(app)  # 注册前置钩子函数
    register_after_hook(app)  # 注册后置钩子函数
    register_errorhandler_hook(app)  # 注册异常捕获钩子函数

    # 注册蓝图
    from apps.api_test.blueprint import api_test
    from apps.ui_test.blueprint import ui_test
    from apps.app_test.blueprint import app_test
    from apps.assist.blueprint import assist
    from apps.test_work.blueprint import test_work
    from apps.config.blueprint import config_blueprint
    from apps.tools.blueprint import tool
    from apps.home.blueprint import home
    from apps.system.blueprint import system_manage
    app.register_blueprint(api_test, url_prefix="/api/apiTest")
    app.register_blueprint(ui_test, url_prefix="/api/webUiTest")
    app.register_blueprint(app_test, url_prefix="/api/appUiTest")
    app.register_blueprint(assist, url_prefix="/api/assist")
    app.register_blueprint(config_blueprint, url_prefix="/api/config")
    app.register_blueprint(test_work, url_prefix="/api/testWork")
    app.register_blueprint(tool, url_prefix="/api/tools")
    app.register_blueprint(home, url_prefix="/api/home")
    app.register_blueprint(system_manage, url_prefix="/api/system")

    from apps.api_test import model_factory
    from apps.ui_test import model_factory
    from apps.app_test import model_factory
    from apps.assist import model_factory
    from apps.test_work import model_factory
    from apps.config import model_factory
    from apps.system import model_factory

    # 把标识为要进行身份验证的接口，注册到对象APP上
    from .base_view import url_required_map
    app.url_required_map = url_required_map

    return app
