from flask import Blueprint

from utils.log import logger

tool = Blueprint('tool', __name__)
tool.logger = logger

from .views import examination, makeUser, mockData
