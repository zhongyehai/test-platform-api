# -*- coding: utf-8 -*-

from flask import Blueprint

from utils.log import logger

api_test = Blueprint('apiTest', __name__)
api_test.logger = logger

from .views import project, module, api, caseSet, case, step, task, report, home
