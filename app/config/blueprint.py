# -*- coding: utf-8 -*-
from flask import Blueprint

config_blueprint = Blueprint("config", __name__)

from app.config.views import config, configType, runEnv, business
