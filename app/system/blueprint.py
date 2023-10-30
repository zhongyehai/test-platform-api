# -*- coding: utf-8 -*-
from ..baseView import Blueprint

system_manage = Blueprint("system", __name__)

from .views import permission, role, user, errorRecord, job
