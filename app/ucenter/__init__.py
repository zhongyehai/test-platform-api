from flask import Blueprint

ucenter = Blueprint('user', __name__)

from .views import user
