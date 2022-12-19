# -*- coding: utf-8 -*-
from flask import Blueprint

assist = Blueprint("Assist", __name__)

from .views import dataPool, errorRecord, file, func, swagger, yapi, hits, callBack
