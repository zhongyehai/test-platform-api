# -*- coding: utf-8 -*-
from flask import Blueprint

test_work = Blueprint("test_work", __name__)

from .views import account, dataBase, kym, weekly
