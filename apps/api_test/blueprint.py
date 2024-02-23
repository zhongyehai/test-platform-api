# -*- coding: utf-8 -*-
from ..base_view import Blueprint

api_test = Blueprint("apiTest", __name__)

from .views import project, module, api, suite, case, step, task, report, stat, dashboard
