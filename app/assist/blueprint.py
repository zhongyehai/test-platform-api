# -*- coding: utf-8 -*-
from ..baseView import Blueprint

assist = Blueprint("Assist", __name__)

from .views import dataPool, errorRecord, file, script, swagger, hits, callBack  # , yapi
