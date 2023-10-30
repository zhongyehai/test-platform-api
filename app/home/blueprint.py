# -*- coding: utf-8 -*-
from ..baseView import Blueprint

home = Blueprint("home", __name__)

from .views import apiTest
