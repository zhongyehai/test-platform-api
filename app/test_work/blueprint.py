# -*- coding: utf-8 -*-
from ..base_view import Blueprint

test_work = Blueprint("test_work", __name__)

from .views import env, kym, weekly, bug_track
