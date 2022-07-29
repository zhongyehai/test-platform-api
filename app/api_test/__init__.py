# -*- coding: utf-8 -*-
from flask import Blueprint

api_test = Blueprint('apiTest', __name__)

from .views import project, module, api, caseSet, case, step, task, report
