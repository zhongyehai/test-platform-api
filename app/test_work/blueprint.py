# -*- coding: utf-8 -*-
from flask import Blueprint

test_work = Blueprint("test_work", __name__)

from .views import env, dataBase, kym, weekly, bugTrack
