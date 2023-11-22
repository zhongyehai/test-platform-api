# -*- coding: utf-8 -*-
from ..base_view import Blueprint

config_blueprint = Blueprint("config", __name__)

from app.config.views import config, config_type, run_env, business
