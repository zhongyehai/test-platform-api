# -*- coding: utf-8 -*-
from ..base_view import Blueprint

home = Blueprint("home", __name__)

from .views import api_test
