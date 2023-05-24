# -*- coding: utf-8 -*-
from flask import Blueprint

app_ui_test = Blueprint("appUiTest", __name__)

from .views import device, project, module, page, element, caseSuite, case, step, task, report
