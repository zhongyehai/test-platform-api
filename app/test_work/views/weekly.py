# -*- coding: utf-8 -*-
from flask import send_from_directory

from app.test_work import test_work
from app.test_work.models.weekly import WeeklyConfigModel, WeeklyModel
from app.test_work.forms.weekly import (
    GetWeeklyConfigListForm, GetWeeklyConfigForm, AddWeeklyConfigForm, ChangeWeeklyConfigForm, DeleteWeeklyConfigForm,
    GetWeeklyListForm, GetWeeklyForm, AddWeeklyForm, ChangeWeeklyForm, DeleteWeeklyForm
)
from app.ucenter.models.user import User
from utils import restful
from app.baseView import BaseMethodView
from utils.globalVariable import TEMP_FILE_ADDRESS
from utils.makeWeekly import make_weekly_excel, make_current_weekly_excel
from utils.required import login_required


@test_work.route('/weeklyConfig/list')
@login_required
def get_weekly_config_list():
    """ 获取产品、项目列表 """
    form = GetWeeklyConfigListForm()
    if form.validate():
        return restful.success('获取成功', data=WeeklyConfigModel.make_pagination(form))
    return restful.fail(form.get_error())


class WeeklyConfigView(BaseMethodView):
    """ 产品、项目管理 """

    def get(self):
        """ 获取产品、项目信息 """
        form = GetWeeklyConfigForm()
        if form.validate():
            return restful.success('获取成功', data=form.conf.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增产品、项目 """
        form = AddWeeklyConfigForm()
        if form.validate():
            weekly_conf = WeeklyConfigModel().create(form.data)
            return restful.success('新增成功', data=weekly_conf.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        """ 修改产品、项目 """
        form = ChangeWeeklyConfigForm()
        if form.validate():
            form.conf.update(form.data)
            return restful.success('修改成功', data=form.conf.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        """ 删除产品、项目 """
        form = DeleteWeeklyConfigForm()
        if form.validate():
            form.conf.delete()
            return restful.success('删除成功')
        return restful.fail(form.get_error())


@test_work.route('/weekly/list')
@login_required
def get_weekly_list():
    """ 获取周报列表 """
    form = GetWeeklyListForm()
    if form.validate():
        return restful.success('获取成功', data=WeeklyModel.make_pagination(form))
    return restful.fail(form.get_error())


@test_work.route('/weekly/download')
@login_required
def weekly_download():
    """ 导出周报 """
    form = GetWeeklyListForm()
    if form.validate():
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
    return restful.fail(form.get_error())


class WeeklyView(BaseMethodView):
    """ 周报管理 """

    def get(self):
        """ 获取周报信息 """
        form = GetWeeklyForm()
        if form.validate():
            return restful.success('获取成功', data=form.weekly.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        """ 新增周报 """
        form = AddWeeklyForm()
        if form.validate():
            weekly_conf = WeeklyModel().create(form.data)
            return restful.success('新增成功', data=weekly_conf.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        """ 修改周报 """
        form = ChangeWeeklyForm()
        if form.validate():
            form.weekly.update(form.data)
            return restful.success('修改成功', data=form.weekly.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        """ 删除周报 """
        form = DeleteWeeklyForm()
        if form.validate():
            form.weekly.delete()
            return restful.success('删除成功')
        return restful.fail(form.get_error())


test_work.add_url_rule('/weeklyConfig', view_func=WeeklyConfigView.as_view('weeklyConfig'))
test_work.add_url_rule('/weekly', view_func=WeeklyView.as_view('weekly'))
