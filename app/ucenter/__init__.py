from flask import Blueprint

from utils.log import logger

ucenter = Blueprint('user', __name__)
ucenter.logger = logger

from .views import user
