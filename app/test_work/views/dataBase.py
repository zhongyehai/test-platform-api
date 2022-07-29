# -*- coding: utf-8 -*-

import os
import time

from flask import request, current_app as app

from app.test_work import test_work
from utils.globalVariable import DB_BACK_UP_ADDRESS


def make_pagination(data_list, pag_size, page_num):
    """ 数据列表分页 """
    start = (page_num - 1) * pag_size
    end = start + pag_size
    return data_list[start: end]


@test_work.route('/db/backUp', methods=['POST'])
def db_back_up():
    """ 执行数据库备份命令 """
    back_up_name = f'api_test{time.strftime("%Y-%m-%d-%H-%M-%S")}.sql'
    os.system(
        f'mysqldump '
        f'-u{app.conf["db"]["user"]} '
        f'-p{app.conf["db"]["password"]} '
        f'--databases {app.conf["db"]["database"]} > {DB_BACK_UP_ADDRESS}/{back_up_name}'
    )
    return app.restful.success('备份成功', data=back_up_name)


@test_work.route('/db/backUp/list', methods=['GET'])
def db_back_up_list():
    """ 数据库备份文件列表 """
    pag_size = request.args.get('pageSize') or app.conf['page']['pageSize']
    page_num = request.args.get('pageNum') or app.conf['page']['pageNum']
    file_list = os.listdir(DB_BACK_UP_ADDRESS)
    filter_list = make_pagination(file_list, int(pag_size), int(page_num))  # 分页
    return app.restful.success('获取成功', data={'data': filter_list, 'total': file_list.__len__()})
