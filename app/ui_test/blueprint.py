# -*- coding: utf-8 -*-
from ..base_view import Blueprint

ui_test = Blueprint("uiTest", __name__)

from .views import project, module, page, element, suite, case, step, task, report
