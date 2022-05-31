#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/12/27 17:14
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
import os
import time

from flask import request

from app.test_work import test_work
from config.config import conf
from app.utils.globalVariable import DB_BACK_UP_ADDRESS
from app.utils import restful
from app.utils.required import login_required


def make_pagination(data_list, pag_size, page_num):
    """ 数据列表分页 """
    start = (page_num - 1) * pag_size
    end = start + pag_size
    return data_list[start: end]


@test_work.route('/db/backUp', methods=['POST'])
@login_required
def db_back_up():
    """ 执行数据库备份命令 """
    back_up_name = f'api_test{time.strftime("%Y-%m-%d-%H-%M-%S")}.sql'
    os.system(
        f'mysqldump '
        f'-u{conf["db"]["user"]} '
        f'-p{conf["db"]["password"]} '
        f'--databases {conf["db"]["database"]} > {DB_BACK_UP_ADDRESS}/{back_up_name}'
    )
    return restful.success('备份成功', data=back_up_name)


@test_work.route('/db/backUp/list', methods=['GET'])
@login_required
def db_back_up_list():
    """ 数据库备份文件列表 """
    pag_size = request.args.get('pageSize') or conf['page']['pageSize']
    page_num = request.args.get('pageNum') or conf['page']['pageNum']
    file_list = os.listdir(DB_BACK_UP_ADDRESS)
    filter_list = make_pagination(file_list, int(pag_size), int(page_num))  # 分页
    return restful.success('获取成功', data={'data': filter_list, 'total': file_list.__len__()})
