""" 封装基类视图，所有视图都继承 flask_restx.Resource 以便生成swagger文档 """
from flask_restx import Resource

from utils.required import login_required, admin_required


class NotLoginView(Resource):
    """ 不需要登录就能访问的视图 """


class LoginRequiredView(Resource):
    """ 要登录才能访问的视图 """
    decorators = [login_required]


class AdminRequiredView(Resource):
    """ 要管理员权限才能访问的视图 """
    decorators = [admin_required]
