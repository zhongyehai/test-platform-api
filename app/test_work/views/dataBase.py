# -*- coding: utf-8 -*-
import os
import time

from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.test_work.blueprint import test_work
from utils.util.fileUtil import DB_BACK_UP_ADDRESS


def make_pagination(data_list, pag_size, page_num):
    """ 数据列表分页 """
    start = (page_num - 1) * pag_size
    end = start + pag_size
    return data_list[start: end]


class DBBackUpView(LoginRequiredView):

    def post(self):
        """ 执行数据库备份命令 """
        back_up_name = f'api_test{time.strftime("%Y-%m-%d-%H-%M-%S")}.sql'
        os.system(
            f'mysqldump '
            f'-u{app.config["DB_USER"]} '
            f'-p{app.config["DB_PASSWORD"]} '
            f'--databases {app.config["DB_DATABASE"]} > {DB_BACK_UP_ADDRESS}/{back_up_name}'
        )
        return app.restful.success("备份成功", data=back_up_name)


class GetDBBackUpListView(LoginRequiredView):

    def get(self):
        """ 数据库备份文件列表 """
        pag_size = request.args.get("pageSize") or app.config["page_size"]
        page_num = request.args.get("pageNum") or app.config["page_num"]
        file_list = os.listdir(DB_BACK_UP_ADDRESS)
        filter_list = make_pagination(file_list, int(pag_size), int(page_num))  # 分页
        return app.restful.success("获取成功", data={"data": filter_list, "total": file_list.__len__()})


test_work.add_url_rule("/db/backUp", view_func=DBBackUpView.as_view("DBBackUpView"))
test_work.add_url_rule("/db/backUp/list", view_func=GetDBBackUpListView.as_view("GetDBBackUpListView"))
