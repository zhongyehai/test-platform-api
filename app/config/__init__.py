# -*- coding: utf-8 -*-
from flask import Blueprint

from utils.log import logger

config = Blueprint('config', __name__)
config.logger = logger

from app.config.views import config as config_view
