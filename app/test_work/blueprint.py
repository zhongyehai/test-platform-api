# -*- coding: utf-8 -*-
from ..baseView import Blueprint

test_work = Blueprint("test_work", __name__)

from .views import env, kym, weekly, bugTrack
