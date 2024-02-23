# -*- coding: utf-8 -*-
import os
import time

from flask import request, send_from_directory, current_app as app

from ..blueprint import assist
from ..forms.file import GetFileListForm, CheckFileIsExistsForm
from utils.util.file_util import CASE_FILE_ADDRESS, CALL_BACK_ADDRESS, TEMP_FILE_ADDRESS, \
    UI_CASE_FILE_ADDRESS, BROWSER_DRIVER_ADDRESS, FileUtil

folders = {
    "case": CASE_FILE_ADDRESS,
    "ui_case": UI_CASE_FILE_ADDRESS,
    "callBack": CALL_BACK_ADDRESS,
    "temp": TEMP_FILE_ADDRESS,
    "driver": BROWSER_DRIVER_ADDRESS,
}


def format_time(atime):
    """ 时间戳转年月日时分秒 """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(atime))


def make_pagination(data_list, pag_size, page_num):
    """ 数据列表分页 """
    start = (page_num - 1) * pag_size
    end = start + pag_size
    return data_list[start: end]


@assist.login_get("/file/list")
def assist_get_file_list():
    """ 文件列表 """
    form = GetFileListForm()
    addr = folders.get(form.file_type, folders.get("case"))
    file_list = os.listdir(addr)
    filter_list = make_pagination(file_list, form.page_size, form.page_num)  # 分页
    parsed_file_list = []
    for file_name in filter_list:
        file_info = os.stat(os.path.join(addr, file_name))
        parsed_file_list.append({
            "name": file_name,  # 文件名
            "size": file_info.st_size,  # 文件文件大小
            "lastVisitTime": format_time(file_info.st_atime),  # 最近一次使用时间
            "LastModifiedTime": format_time(file_info.st_mtime),  # 最后一次更新时间
        })
    return app.restful.get_success({"data": parsed_file_list, "total": file_list.__len__()})


@assist.login_get("/file/check")
def assist_check_file():
    """ 检查文件是否已存在 """
    form = CheckFileIsExistsForm()
    return app.restful.fail(f"文件 {form.file_name} 已存在") if os.path.exists(
        os.path.join(folders.get(form.file_type, "case"), form.file_name)) else app.restful.success("文件不存在")


@assist.login_get("/file/download")
def assist_download_file():
    """ 下载文件 """
    form = CheckFileIsExistsForm()
    folder_path = folders.get(form.file_type, "case")
    if os.path.exists(os.path.join(folder_path, form.file_name)):
        return send_from_directory(folder_path, form.file_name, as_attachment=True)
    return app.restful.fail("文件不存在")


@assist.login_post("/file/upload")
def assist_upload_file():
    """ 文件上传 """
    file, addr = request.files["file"], folders.get(request.form.get("file_type", "case"))
    file.save(os.path.join(addr, file.filename))
    return app.restful.upload_success(file.filename)


@assist.login_get("/file")
def assist_get_file():
    """ 获取文件 """
    args = request.args.to_dict()
    return send_from_directory(args.get("file_type", "case"), args.get("name"), as_attachment=True)


@assist.login_post("/file")
def assist_add_file():
    """ 上传文件 """
    file_name_list, addr = [], folders.get(request.form.get("file_type", "case"))
    for file_io in request.files.getlist("files"):
        file_io.save(os.path.join(addr, file_io.filename))
        file_name_list.append(file_io.filename)
    return app.restful.upload_success(file_name_list)


@assist.login_delete("/file")
def assist_delete_file():
    """ 删除文件 """
    form = CheckFileIsExistsForm()
    path = os.path.join(folders.get(form.file_type, "case"), form.file_name)
    FileUtil.delete_file(path)
    return app.restful.delete_success()
