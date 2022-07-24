from flask import Blueprint

from utils.log import logger

ui_test = Blueprint('uiTest', __name__)
ui_test.logger = logger

from .views import project, module, page, element, caseSet, case, step, task, report
