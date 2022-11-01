# -*- coding: utf-8 -*-
from flask import send_from_directory, current_app as app

from app.baseView import LoginRequiredView
from app.test_work.blueprint import test_work
from app.test_work.models.weekly import WeeklyConfigModel, WeeklyModel
from app.test_work.forms.weekly import (
    GetWeeklyConfigListForm, GetWeeklyConfigForm, AddWeeklyConfigForm, ChangeWeeklyConfigForm, DeleteWeeklyConfigForm,
    GetWeeklyListForm, GetWeeklyForm, AddWeeklyForm, ChangeWeeklyForm, DeleteWeeklyForm
)
from app.system.models.user import User
from utils.util.fileUtil import TEMP_FILE_ADDRESS
from utils.makeData.makeWeekly import make_weekly_excel, make_current_weekly_excel


class GetWeeklyConfigListView(LoginRequiredView):

    def get(self):
        """ 获取产品、项目列表 """
        form = GetWeeklyConfigListForm().do_validate()
        return app.restful.success('获取成功', data=WeeklyConfigModel.make_pagination(form))


class WeeklyConfigView(LoginRequiredView):
    """ 产品、项目管理 """

    def get(self):
        """ 获取产品、项目信息 """
        form = GetWeeklyConfigForm().do_validate()
        return app.restful.success('获取成功', data=form.conf.to_dict())

    def post(self):
        """ 新增产品、项目 """
        form = AddWeeklyConfigForm().do_validate()
        weekly_conf = WeeklyConfigModel().create(form.data)
        return app.restful.success('新增成功', data=weekly_conf.to_dict())

    def put(self):
        """ 修改产品、项目 """
        form = ChangeWeeklyConfigForm().do_validate()
        form.conf.update(form.data)
        return app.restful.success('修改成功', data=form.conf.to_dict())

    def delete(self):
        """ 删除产品、项目 """
        form = DeleteWeeklyConfigForm().do_validate()
        form.conf.delete()
        return app.restful.success('删除成功')


class GetWeeklyListView(LoginRequiredView):

    def get(self):
        """ 获取周报列表 """
        form = GetWeeklyListForm().do_validate()
        return app.restful.success('获取成功', data=WeeklyModel.make_pagination(form))


class GetWeeklyDownloadView(LoginRequiredView):

    def get(self):
        """ 导出周报 """
        form = GetWeeklyListForm().do_validate()
        form.pageNum.data = form.pageSize.data = ''

        # 获取产品、项目数据
        product_dict = WeeklyConfigModel.get_data_dict()
        user_dict = {user.id: user.name for user in User.get_all()}

        if form.download_type.data == 'current':  # 导出本周周报
            data_list = WeeklyModel.make_pagination(form)
            file_name = make_current_weekly_excel(product_dict, data_list, user_dict)  # 生成excel
        else:  # 导出指定时间段的周报
            data_list = WeeklyModel.make_pagination(form)
            file_name = make_weekly_excel(data_list, form, user_dict)
        return send_from_directory(TEMP_FILE_ADDRESS, file_name, as_attachment=True)


class WeeklyView(LoginRequiredView):
    """ 周报管理 """

    def get(self):
        """ 获取周报信息 """
        form = GetWeeklyForm().do_validate()
        return app.restful.success('获取成功', data=form.weekly.to_dict())

    def post(self):
        """ 新增周报 """
        form = AddWeeklyForm().do_validate()
        weekly_conf = WeeklyModel().create(form.data)
        return app.restful.success('新增成功', data=weekly_conf.to_dict())

    def put(self):
        """ 修改周报 """
        form = ChangeWeeklyForm().do_validate()
        form.weekly.update(form.data)
        return app.restful.success('修改成功', data=form.weekly.to_dict())

    def delete(self):
        """ 删除周报 """
        form = DeleteWeeklyForm().do_validate()
        form.weekly.delete()
        return app.restful.success('删除成功')


test_work.add_url_rule('/weekly', view_func=WeeklyView.as_view('WeeklyView'))
test_work.add_url_rule('/weekly/list', view_func=GetWeeklyListView.as_view('GetWeeklyListView'))
test_work.add_url_rule('/weekly/config', view_func=WeeklyConfigView.as_view('WeeklyConfigView'))
test_work.add_url_rule('/weekly/download', view_func=GetWeeklyDownloadView.as_view('GetWeeklyDownloadView'))
test_work.add_url_rule('/weekly/config/list', view_func=GetWeeklyConfigListView.as_view('GetWeeklyConfigListView'))
