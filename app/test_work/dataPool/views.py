#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
from app.utils.required import login_required
from app.test_work import test_work
from .models import AutoTestPolyFactoring, AutoTestUser
from app.utils import restful


@test_work.route('/dataPool')
@login_required
def data_pool_list():
    """ 数据池数据列表 """
    return restful.success('获取成功', data=[
        data_pool.to_dict(pop_list=['created_time', 'update_time']) for data_pool in
        AutoTestPolyFactoring.query.filter().order_by(AutoTestPolyFactoring.id.desc()).all()
    ])


@test_work.route('/autoTestUser')
@login_required
def auto_test_user_list():
    """ 自动化测试用户数据列表 """
    return restful.success('获取成功', data=[
        user.to_dict(pop_list=['created_time', 'update_time']) for user in AutoTestUser.query.filter().all()
    ])
