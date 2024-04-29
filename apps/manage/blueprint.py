# -*- coding: utf-8 -*-
from ..base_view import Blueprint

manage = Blueprint("manage", __name__)

from .views import env, kym, weekly, bug_track, todo
