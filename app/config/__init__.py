# -*- coding: utf-8 -*-
from flask import Blueprint

config = Blueprint('config', __name__)

from app.config.views import config as config_view
