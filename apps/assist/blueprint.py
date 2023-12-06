# -*- coding: utf-8 -*-
from ..base_view import Blueprint

assist = Blueprint("Assist", __name__)

from .views import data_pool, error_record, file, script, swagger, hits, call_back, queue
