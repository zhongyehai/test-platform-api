# -*- coding: utf-8 -*-

from flask import current_app as app, request
from app.assist import assist
from app.config.models.config import Config
from app.assist.models.dataPool import AutoTestPolyFactoring, AutoTestUser


@assist.route('/dataPool')
def data_pool_list():
    """ 数据池数据列表 """
    return app.restful.success('获取成功', data=[
        data_pool.to_dict(pop_list=['created_time', 'update_time']) for data_pool in
        AutoTestPolyFactoring.query.filter().order_by(AutoTestPolyFactoring.id.desc()).all()
    ])


@assist.route('/autoTestUser')
def auto_test_user_list():
    """ 自动化测试用户数据列表 """
    return app.restful.success('获取成功', data=[
        auto_user.to_dict(pop_list=['created_time', 'update_time']) for auto_user in
        AutoTestUser.get_all(env=request.args.get('env', 'test'))
    ])


@assist.route('/env/list')
def get_env_list():
    """ 获取环境列表 """
    return app.restful.success('获取成功', data=Config.loads(Config.get_first(name='run_test_env').value))
