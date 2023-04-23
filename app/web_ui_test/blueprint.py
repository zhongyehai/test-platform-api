# -*- coding: utf-8 -*-
from flask import Blueprint

web_ui_test = Blueprint("uiTest", __name__)

from .views import project, module, page, element, caseSuite, case, step, task, report
