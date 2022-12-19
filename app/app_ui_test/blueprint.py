# -*- coding: utf-8 -*-
from flask import Blueprint

app_ui_test = Blueprint("appUiTest", __name__)

from .views import env, project, module, page, element, caseSet, case, step, task, report
