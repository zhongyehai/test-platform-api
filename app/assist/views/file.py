# -*- coding: utf-8 -*-
import os
import time

from flask import request, send_from_directory, current_app as app

from app.assist.blueprint import assist
from utils.util.fileUtil import CASE_FILE_ADDRESS, CALL_BACK_ADDRESS, TEMP_FILE_ADDRESS, \
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
    pag_size = request.args.get("pageSize") or app.config["page_size"]
    page_num = request.args.get("pageNum") or app.config["page_num"]
    addr = folders.get(request.args.get("fileType"), "case")
    file_list = os.listdir(addr)
    filter_list = make_pagination(file_list, int(pag_size), int(page_num))  # 分页
    parsed_file_list = []
    for file_name in filter_list:
        file_info = os.stat(os.path.join(addr, file_name))
        parsed_file_list.append({
            "name": file_name,  # 文件名
            "size": file_info.st_size,  # 文件文件大小
            "lastVisitTime": format_time(file_info.st_atime),  # 最近一次使用时间
            "LastModifiedTime": format_time(file_info.st_mtime),  # 最后一次更新时间
        })
    return app.restful.success("获取成功", data={"data": parsed_file_list, "total": file_list.__len__()})


@assist.login_get("/file/check")
def assist_check_file():
    """ 检查文件是否已存在 """
    file_name, file_type = request.args.get("name"), request.args.get("fileType")
    return app.restful.fail(f"文件 {file_name} 已存在") if os.path.exists(
        os.path.join(folders.get(file_type, "case"), file_name)) else app.restful.success("文件不存在")


@assist.login_get("/file/download")
def assist_download_file():
    """ 下载文件 """
    addr = folders.get(request.args.get("fileType"), "case")
    return send_from_directory(addr, request.args.to_dict().get("name"), as_attachment=True)


@assist.login_post("/file/upload")
def assist_upload_file():
    """ 文件上传 """
    file, addr = request.files["file"], folders.get(request.form.get("fileType", "case"))
    file.save(os.path.join(addr, file.filename))
    return app.restful.success(msg="上传成功", data=file.filename)


@assist.login_get("/file")
def assist_get_file():
    """ 获取文件 """
    args = request.args.to_dict()
    return send_from_directory(args.get("fileType", "case"), args.get("name"), as_attachment=True)


@assist.login_post("/file")
def assist_add_file():
    """ 上传文件 """
    file_name_list, addr = [], folders.get(request.form.get("fileType", "case"))
    for file_io in request.files.getlist("files"):
        file_io.save(os.path.join(addr, file_io.filename))
        file_name_list.append(file_io.filename)
    return app.restful.success(msg="上传成功", data=file_name_list)


@assist.login_delete("/file")
def assist_delete_file():
    """ 删除文件 """
    request_json = request.get_json(silent=True)
    name, addr = request_json.get("name"), folders.get(request_json.get("fileType"), "case")
    path = os.path.join(addr, name)
    FileUtil.delete_file(path)
    return app.restful.success("删除成功", data={"name": name})
