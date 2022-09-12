from flask import Blueprint
from flask_restx import Api

web_ui_test_blueprint = Blueprint('uiTest', __name__)

web_ui_test = Api(
    web_ui_test_blueprint,
    version="1.0",
    doc="/swagger",
    title="webUI自动化测试管理",
    description="webUI自动化测试管理相关接口"
)

from .views import project, module, page, element, caseSet, case, step, task, report
