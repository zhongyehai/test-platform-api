from flask import Blueprint

from utils.log import logger

test_work = Blueprint('test_work', __name__)
test_work.logger = logger

from .views import account, dataBase, kym, weekly
