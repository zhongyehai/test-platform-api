from flask import Blueprint
from flask_restx import Api

tool_blueprint = Blueprint('tool', __name__)
tool = Api(
    tool_blueprint,
    version="1.0",
    doc="/swagger",
    title="工具管理",
    description="工具管理相关接口"
)


from .views import examination, makeUser, mockData
