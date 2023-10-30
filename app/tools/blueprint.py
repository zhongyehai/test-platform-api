# -*- coding: utf-8 -*-
from ..baseView import Blueprint

tool = Blueprint("tools", __name__)

from .views import examination, makeUser, mockData
