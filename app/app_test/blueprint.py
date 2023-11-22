# -*- coding: utf-8 -*-
from ..base_view import Blueprint

app_test = Blueprint("appUiTest", __name__)

from .views import device, project, module, page, element, suite, case, step, task, report
