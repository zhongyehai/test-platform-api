from flask import Blueprint
from flask_restx import Api

test_work_blueprint = Blueprint('test_work', __name__)
test_work = Api(
    test_work_blueprint,
    version="1.0",
    doc="/swagger",
    title="测试管理",
    description="测试管理相关接口"
)


from .views import account, dataBase, kym, weekly
