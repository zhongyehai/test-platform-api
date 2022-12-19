# -*- coding: utf-8 -*-
from flask import Blueprint

system_manage = Blueprint("system", __name__)

from .views import errorRecord, role, user, business
