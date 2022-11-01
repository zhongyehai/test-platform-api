""" 封装基类视图，所有视图都继承 flask_restx.Resource 以便生成swagger文档 """
from flask.views import MethodView

from utils.view.required import login_required, admin_required


class NotLoginView(MethodView):
    """ 不需要登录就能访问的视图 """


class LoginRequiredView(MethodView):
    """ 要登录才能访问的视图 """
    decorators = [login_required]


class AdminRequiredView(MethodView):
    """ 要管理员权限才能访问的视图 """
    decorators = [admin_required]
