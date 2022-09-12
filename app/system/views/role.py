# -*- coding: utf-8 -*-
from flask import current_app as app

from app.baseView import AdminRequiredView
from app.system import system_manage
from app.system.models.user import Role


ns = system_manage.namespace("role", description="权限管理相关接口")


@ns.route('/list/')
class GetRoleListView(AdminRequiredView):

    def get(self):
        """ 获取角色列表 """
        return app.restful.success(data=[{'id': role.id, 'name': role.name} for role in Role.get_all()])
