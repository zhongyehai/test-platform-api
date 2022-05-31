# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:02
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
import json
import os

from flask import request, send_from_directory

from app.test_work import test_work
from app.utils.globalVariable import TEMP_FILE_ADDRESS
from app.utils.makeXmind import make_xmind
from .models import KYMModule, db
from app.config.models import Config
from app.utils import restful
from app.baseView import BaseMethodView
from app.utils.required import login_required


@test_work.route('/kym/project', methods=['POST'])
@login_required
def add_kym_project():
    """ kym添加服务 """
    if KYMModule.get_first(project=request.json['project']):
        return restful.fail(f"服务 {request.json['project']} 已存在")
    with db.auto_commit():
        kym_data = {"nodeData": {"topic": request.json['project'], "root": True, "children": []}}
        kym_data['nodeData']['children'] = json.loads(Config.get_first(name='kym').value)
        kym = KYMModule()
        kym.create({'project': request.json['project'], 'kym': json.dumps(kym_data, ensure_ascii=False, indent=4)})
        db.session.add(kym)
    return restful.success('新增成功', data=kym.to_dict())


@test_work.route('/kym/project/list')
@login_required
def get_kym_project_list():
    """ kym服务列表 """
    project_list = KYMModule.query.with_entities(KYMModule.project).distinct().all()
    return restful.success('获取成功', data=[{'key': project[0], 'value': project[0]} for project in project_list])


@test_work.route('/kym/download', methods=['GET'])
@login_required
def export_kym_as_xmind():
    """ 导出为xmind """
    project = KYMModule.get_first(project=request.args.get("project"))
    file_path = os.path.join(TEMP_FILE_ADDRESS, f'{project.project}.xmind')
    if os.path.exists(file_path):
        os.remove(file_path)
    make_xmind(file_path, json.loads(project.kym))
    return send_from_directory(TEMP_FILE_ADDRESS, f'{project.project}.xmind', as_attachment=True)


class KYMView(BaseMethodView):
    """ KYM管理 """

    def get(self):
        """ 获取KYM """
        return restful.success('获取成功', data=KYMModule.get_first(project=request.args.get('project')).to_dict())

    def put(self):
        """ 修改KYM号 """
        kym = KYMModule.get_first(project=request.json['project'])
        kym.update({'kym': json.dumps(request.json['kym'], ensure_ascii=False, indent=4)})
        return restful.success('修改成功', data=kym.to_dict())


test_work.add_url_rule('/kym', view_func=KYMView.as_view('kym'))
