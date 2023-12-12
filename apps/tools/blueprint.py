# -*- coding: utf-8 -*-
from ..base_view import Blueprint

tool = Blueprint("tools", __name__)

from .views import examination, make_user, mock_data, parse_token
