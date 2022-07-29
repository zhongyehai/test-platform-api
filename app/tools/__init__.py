from flask import Blueprint

tool = Blueprint('tool', __name__)

from .views import examination, makeUser, mockData
