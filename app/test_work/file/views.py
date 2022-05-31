#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/6/28 10:06
# @Author : ZhongYeHai
# @Site : 
# @File : fileView.py
# @Software: PyCharm
import os
import time

from flask import request, send_from_directory

from config.config import conf
from app.test_work import test_work
from app.utils import restful
from app.utils.globalVariable import CASE_FILE_ADDRESS, CALL_BACK_ADDRESS, CFCA_FILE_ADDRESS, TEMP_FILE_ADDRESS
from app.baseView import BaseMethodView
from app.utils.required import login_required

folders = {
    'case': CASE_FILE_ADDRESS,
    'cfca': CFCA_FILE_ADDRESS,
    'callBack': CALL_BACK_ADDRESS,
    'temp': TEMP_FILE_ADDRESS,
}


def format_time(atime):
    """ 时间戳转年月日时分秒 """
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(atime))


@test_work.route('/file/create/download')
def creat_file():
    """ 创建指定大小和格式的文件 """
    start = time.time()
    size, file_format = float(request.args.get('size')), request.args.get('format')
    local_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    file_name = f"temp_file_{str(local_time)}.{file_format}"

    # 删除历史的大文件
    for old_file in os.listdir(TEMP_FILE_ADDRESS):
        if old_file.startswith('temp_file'):
            os.remove(os.path.join(TEMP_FILE_ADDRESS, old_file))

    # 生成新的大文件
    file = open(os.path.join(TEMP_FILE_ADDRESS, file_name), 'w', encoding='utf-8')
    file.seek(1024 * 1024 * 1024 * size)
    file.write('test')
    file.close()
    print(time.time() - start)
    return send_from_directory(TEMP_FILE_ADDRESS, file_name, as_attachment=True)


def make_pagination(data_list, pag_size, page_num):
    """ 数据列表分页 """
    start = (page_num - 1) * pag_size
    end = start + pag_size
    return data_list[start: end]


@test_work.route('/file/list')
@login_required
def get_file_list():
    """ 文件列表 """
    pag_size = request.args.get('pageSize') or conf['page']['pageSize']
    page_num = request.args.get('pageNum') or conf['page']['pageNum']
    addr = folders.get(request.args.get('fileType'), 'case')
    file_list = os.listdir(addr)

    # 分页
    filter_list = make_pagination(file_list, int(pag_size), int(page_num))

    parsed_file_list = []
    for file_name in filter_list:
        file_info = os.stat(os.path.join(addr, file_name))
        parsed_file_list.append({
            'name': file_name,  # 文件名
            'size': file_info.st_size,  # 文件文件大小
            'lastVisitTime': format_time(file_info.st_atime),  # 最近一次使用时间
            'LastModifiedTime': format_time(file_info.st_mtime),  # 最后一次更新时间
        })
    return restful.success('获取成功', data={'data': parsed_file_list, 'total': file_list.__len__()})


@test_work.route('/file/check', methods=['GET'])
@login_required
def check_file():
    """ 检查文件是否已存在 """
    file_name, file_type = request.args.get('name'), request.args.get('fileType')
    return restful.fail(f'文件 {file_name} 已存在') if os.path.exists(
        os.path.join(folders.get(file_type), file_name)) else restful.success('文件不存在')


@test_work.route('/file/download', methods=['GET'])
@login_required
def download_file():
    """ 下载文件 """
    addr = folders.get(request.args.get('fileType'), 'case')
    return send_from_directory(addr, request.args.to_dict().get('name'), as_attachment=True)


@test_work.route('/upload', methods=['POST'], strict_slashes=False)
@login_required
def file_upload():
    """ 文件上传 """
    file, addr = request.files['file'], folders.get(request.form.get('fileType', 'case'))
    file.save(os.path.join(addr, file.filename))
    return restful.success(msg='上传成功', data=file.filename)


class FileManage(BaseMethodView):
    """ 文件管理视图 """

    decorators = []

    def get(self):
        args = request.args.to_dict()
        return send_from_directory(args.get('fileType', 'case'), args.get('name'), as_attachment=True)

    def post(self):
        """ 上传文件 """
        file_name_list, addr = [], folders.get(request.form.get('fileType', 'case'))
        for file_io in request.files.getlist('files'):
            file_io.save(os.path.join(addr, file_io.filename))
            file_name_list.append(file_io.filename)
        return restful.success(msg='上传成功', data=file_name_list)

    def delete(self):
        """ 删除文件 """
        request_json = request.get_json(silent=True)
        name, addr = request_json.get('name'), folders.get(request_json.get('fileType'), 'case')
        path = os.path.join(addr, name)
        if os.path.exists(path):
            os.remove(path)
        return restful.success('删除成功', data={'name': name})


test_work.add_url_rule('/file', view_func=FileManage.as_view('file'))
