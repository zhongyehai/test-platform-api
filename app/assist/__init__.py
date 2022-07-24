# -*- coding: utf-8 -*-

from flask import Blueprint

from utils.log import logger

assist = Blueprint('Assist', __name__)
assist.logger = logger

from .views import dataPool, errorRecord, file, func, swagger, yapi
