# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import AdminRequiredView
from app.system.blueprint import system_manage
from app.system.models.user import Role


class GetRoleListView(AdminRequiredView):

    def get(self):
        """ 获取角色列表 """
        return app.restful.success(data=[{'id': role.id, 'name': role.name} for role in Role.get_all()])


system_manage.add_url_rule('/role/list', view_func=GetRoleListView.as_view('GetRoleListView'))
