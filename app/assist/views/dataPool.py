# -*- coding: utf-8 -*-

from flask import request
from utils.required import login_required
from app.assist import assist
from app.config.models.config import Config
from app.assist.models.dataPool import AutoTestPolyFactoring, AutoTestUserDev, AutoTestUserTest, AutoTestUserUat, AutoTestUserProduction
from utils import restful

user_db_dict = {
    'dev': AutoTestUserDev,
    'test': AutoTestUserTest,
    'uat': AutoTestUserUat,
    'production': AutoTestUserProduction
}


@assist.route('/dataPool')
@login_required
def data_pool_list():
    """ 数据池数据列表 """
    return restful.success('获取成功', data=[
        data_pool.to_dict(pop_list=['created_time', 'update_time']) for data_pool in
        AutoTestPolyFactoring.query.filter().order_by(AutoTestPolyFactoring.id.desc()).all()
    ])


@assist.route('/autoTestUser')
@login_required
def auto_test_user_list():
    """ 自动化测试用户数据列表 """
    return restful.success('获取成功', data=[
        user.to_dict(pop_list=['created_time', 'update_time']) for user in
        user_db_dict.get(request.args.get('env'), 'test').query.filter().all()
    ])


@assist.route('/env/list')
@login_required
def get_env_list():
    """ 获取环境列表 """
    return restful.success('获取成功', data=Config.loads(Config.get_first(name='run_test_env').value))
