# -*- coding: utf-8 -*-

from flask import request
from app.utils.required import login_required
from app.test_work import test_work
from app.test_work.models.dataPool import AutoTestPolyFactoring, AutoTestUserDev, AutoTestUserTest, AutoTestUserUat, AutoTestUserProduction
from app.utils import restful

user_dict = {
    'dev': AutoTestUserDev,
    'test': AutoTestUserTest,
    'uat': AutoTestUserUat,
    'production': AutoTestUserProduction
}


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
        user.to_dict(pop_list=['created_time', 'update_time']) for user in
        user_dict.get(request.args.get('env'), 'test').query.filter().all()
    ])


@test_work.route('/env/list')
@login_required
def get_env_list():
    """ 获取环境列表 """
    return restful.success('获取成功', data=['dev', 'test', 'uat', 'production'])
