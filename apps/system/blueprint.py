# -*- coding: utf-8 -*-
from ..base_view import Blueprint

system_manage = Blueprint("system", __name__)

from .views import permission, role, user, error_record, job, sso, package
