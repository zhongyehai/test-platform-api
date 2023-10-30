# -*- coding: utf-8 -*-
import json
import os

from flask import request, send_from_directory, current_app as app

from app.test_work.blueprint import test_work
from utils.util.fileUtil import TEMP_FILE_ADDRESS, FileUtil
from utils.makeData.makeXmind import make_xmind
from app.test_work.models.kym import KYMModule, db
from app.config.models.config import Config


@test_work.login_get("/kym/project/list")
def test_work_get_kym_project_list():
    """ kym服务列表 """
    project_list = KYMModule.query.with_entities(KYMModule.project).distinct().all()
    return app.restful.success("获取成功",
                               data=[{"key": project[0], "value": project[0]} for project in project_list])


@test_work.login_post("/kym/project")
def test_work_get_kym_project():
    """ kym添加服务 """
    if KYMModule.get_first(project=request.json["project"]):
        return app.restful.fail(f'服务 {request.json["project"]} 已存在')
    with db.auto_commit():
        kym_data = {"nodeData": {"topic": request.json["project"], "root": True, "children": []}}
        kym_data["nodeData"]["children"] = Config.get_kym()
        kym = KYMModule()
        kym.create({"project": request.json["project"], "kym": kym_data})
        db.session.add(kym)
    return app.restful.success("新增成功", data=kym.to_dict())


@test_work.login_get("/kym/download")
def test_work_download_kym():
    """ 导出为xmind """
    project = KYMModule.get_first(project=request.args.get("project"))
    file_path = os.path.join(TEMP_FILE_ADDRESS, f"{project.project}.xmind")
    FileUtil.delete_file(file_path)
    make_xmind(file_path, json.loads(project.kym))
    return send_from_directory(TEMP_FILE_ADDRESS, f"{project.project}.xmind", as_attachment=True)


@test_work.login_get("/kym")
def test_work_get_kym():
    """ 获取KYM """
    return app.restful.success("获取成功", data=KYMModule.get_first(project=request.args.get("project")).to_dict())


@test_work.login_put("/kym")
def test_work_change_kym():
    """ 修改KYM号 """
    kym = KYMModule.get_first(project=request.json["project"])
    kym.update({"kym": json.dumps(request.json["kym"], ensure_ascii=False, indent=4)})
    return app.restful.success("修改成功", data=kym.to_dict())
