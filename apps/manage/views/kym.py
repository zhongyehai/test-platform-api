# -*- coding: utf-8 -*-
import os

from flask import request, send_from_directory, current_app as app

from ..blueprint import manage
from ..forms.kym import KymProjectForm, ChangeKymForm
from ..model_factory import KYMModule
from ...config.model_factory import Config
from utils.make_data.make_xmind import make_xmind
from utils.util.file_util import TEMP_FILE_ADDRESS, FileUtil


@manage.login_get("/kym/project/list")
def manage_get_kym_project_list():
    """ kym服务列表 """
    project_list = KYMModule.query.with_entities(KYMModule.project).distinct().all()
    return app.restful.get_success([{"key": project[0], "value": project[0]} for project in project_list])


@manage.login_post("/kym/project")
def manage_get_kym_project():
    """ kym添加服务 """
    if KYMModule.get_first(project=request.json["project"]):
        return app.restful.fail(f'服务 {request.json["project"]} 已存在')
    kym_data = {"nodeData": {"topic": request.json["project"], "root": True, "children": []}}
    kym_data["nodeData"]["children"] = Config.get_kym()
    kym = KYMModule.model_create_and_get({"project": request.json["project"], "kym": kym_data})
    return app.restful.add_success(kym.to_dict())


@manage.login_get("/kym/download")
def manage_download_kym():
    """ 导出为xmind """
    project = KYMModule.get_first(project=request.args.get("project"))
    file_path = os.path.join(TEMP_FILE_ADDRESS, f"{project.project}.xmind")
    FileUtil.delete_file(file_path)
    make_xmind(file_path, project.kym)
    return send_from_directory(TEMP_FILE_ADDRESS, f"{project.project}.xmind", as_attachment=True)


@manage.login_get("/kym")
def manage_get_kym():
    """ 获取KYM """
    form = KymProjectForm()
    return app.restful.get_success(KYMModule.get_first(project=form.project).to_dict())


@manage.login_put("/kym")
def manage_change_kym():
    """ 修改KYM号 """
    form = ChangeKymForm()
    KYMModule.query.filter(KYMModule.project == form.project).update({"kym": form.kym})
    return app.restful.change_success()
